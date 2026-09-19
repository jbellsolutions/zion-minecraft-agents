"""Deployment invariants tested without Java, network, or a real Minecraft world."""
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

SPEC = importlib.util.spec_from_file_location("zion_deploy", Path(__file__).parents[1] / "tools/zion_deploy.py")
d = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(d)


class FakeRuntime(d.Runtime):
    def __init__(self, root):
        (root / "server/mods").mkdir(parents=True)
        (root / "client/mods").mkdir(parents=True)
        super().__init__({"server_root": str(root / "server"), "client_mods": str(root / "client/mods")})
        self.active = True
        self.fail_start = 0
        self.fail_stop = False
        self.events = []

    def owned(self):
        return {"pid": 99} if self.active else None

    def running(self):
        return [self.owned()] if self.active else []

    def client_processes(self):
        return []

    def stop(self):
        self.events.append("stop")
        if self.fail_stop:
            raise d.DeployError("Still shutting down")
        self.active = False

    def start(self):
        self.events.append("start")
        if self.fail_start:
            self.fail_start -= 1
            raise d.DeployError("New mod crashed")
        self.active = True
        return {"ready": True}


class DeployTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        validator = patch.object(d, "validate_manifest", return_value=[])
        self.validator = validator.start()
        self.addCleanup(validator.stop)
        self.runtime = FakeRuntime(self.root)
        self.jar = self.root / "new.jar"
        with zipfile.ZipFile(self.jar, "w") as z:
            z.writestr("META-INF/mods.toml", "modLoader='javafml'")
            z.writestr("example/Example.class", b"compiled fixture")
        self.manifest = {"schema_version": 1, "job_id": "sword", "minecraft": "1.21.4", "forge": "54.1.0", "artifacts": [{"kind": "mod", "source": "new.jar", "filename": "sword-2.jar", "sha256": d.digest(self.jar), "validation": {"build": True, "assets": True}}]}
        self.creation()
        self.legacy = self.runtime.server / "mods/legacy.jar"
        self.legacy.write_bytes(b"unrelated")
        self.world = self.runtime.server / "world/region/r.0.0.mca"
        self.world.parent.mkdir(parents=True)
        self.world.write_bytes(b"player world")

    def creation(self):
        """Manifest validation has its own suite; isolate filesystem transactions here."""
        path = self.root / "creation.json"
        path.write_text(json.dumps({"artifacts": [{"path": a["source"], "sha256": a["sha256"], "kind": "jar" if a["kind"] == "mod" else "datapack"} for a in self.manifest["artifacts"]], "evidence": [{"check": "compile", "status": "passed", "artifact_sha256": a["sha256"]} for a in self.manifest["artifacts"]]}))
        self.manifest.update(creation_manifest="creation.json", creation_sha256=d.digest(path))

    def check_preserved(self):
        self.assertEqual(self.legacy.read_bytes(), b"unrelated")
        self.assertEqual(self.world.read_bytes(), b"player world")

    def test_install_and_exact_rollback_preserve_legacy_world_and_later_mod(self):
        journal = d.deploy(self.runtime, self.manifest, self.root)
        self.assertEqual(journal["status"], "deployed")
        for folder in (self.runtime.server / "mods", self.runtime.client):
            self.assertEqual(d.digest(folder / "sword-2.jar"), d.digest(self.jar))
        (self.runtime.server / "mods/later.jar").write_bytes(b"later")
        d.rollback(self.runtime, journal["id"])
        self.assertFalse((self.runtime.client / "sword-2.jar").exists())
        self.assertEqual((self.runtime.server / "mods/later.jar").read_bytes(), b"later")
        self.check_preserved()

    def test_failed_start_restores_replaced_files_on_both_sides(self):
        for folder in (self.runtime.server / "mods", self.runtime.client):
            (folder / "sword-1.jar").write_bytes(b"old")
        old = self.runtime.client / "sword-1.jar"
        self.manifest["artifacts"][0]["replaces"] = [{"filename": "sword-1.jar", "sha256": d.digest(old)}]
        self.runtime.fail_start = 1
        with self.assertRaisesRegex(d.DeployError, "previous tracked files restored"):
            d.deploy(self.runtime, self.manifest, self.root)
        for folder in (self.runtime.server / "mods", self.runtime.client):
            self.assertEqual((folder / "sword-1.jar").read_bytes(), b"old")
            self.assertFalse((folder / "sword-2.jar").exists())
        self.assertTrue(self.runtime.active)
        self.check_preserved()

    def test_failed_stop_leaves_installed_files_untouched(self):
        self.runtime.fail_stop = True
        with self.assertRaisesRegex(d.DeployError, "shutting down"):
            d.deploy(self.runtime, self.manifest, self.root)
        self.assertFalse((self.runtime.server / "mods/sword-2.jar").exists())
        self.assertEqual(self.runtime.events, ["stop"])
        self.check_preserved()

    def test_changed_file_blocks_rollback_before_stopping(self):
        journal = d.deploy(self.runtime, self.manifest, self.root)
        changed = self.runtime.server / "mods/sword-2.jar"
        changed.write_bytes(b"someone else updated this")
        before = list(self.runtime.events)
        with self.assertRaisesRegex(d.DeployError, "Rollback conflict"):
            d.rollback(self.runtime, journal["id"])
        self.assertEqual(self.runtime.events, before)
        self.assertEqual(changed.read_bytes(), b"someone else updated this")

    def test_wrong_hash_and_collision_rejected_before_stop(self):
        self.manifest["artifacts"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(d.DeployError, "hash mismatch"):
            d.deploy(self.runtime, self.manifest, self.root)
        self.manifest["artifacts"][0]["sha256"] = d.digest(self.jar)
        (self.runtime.server / "mods/sword-2.jar").write_bytes(b"unknown old version")
        with self.assertRaisesRegex(d.DeployError, "explicit replacement"):
            d.deploy(self.runtime, self.manifest, self.root)
        self.assertEqual(self.runtime.events, [])

    def test_path_traversal_and_symlink_rejected(self):
        self.manifest["artifacts"][0]["filename"] = "../outside.jar"
        with self.assertRaises(d.DeployError):
            d.build_plan(self.runtime, self.manifest, self.root)
        self.manifest["artifacts"][0]["filename"] = "sword-2.jar"
        (self.runtime.client / "sword-2.jar").symlink_to(self.legacy)
        with self.assertRaisesRegex(d.DeployError, "Symlink"):
            d.build_plan(self.runtime, self.manifest, self.root)
        self.check_preserved()

    def test_lock_prevents_concurrent_deploy(self):
        with self.runtime.lock():
            with self.assertRaisesRegex(d.DeployError, "owns the server lock"):
                d.deploy(self.runtime, self.manifest, self.root)

    def test_datapack_installs_only_archive_not_world(self):
        pack = self.root / "pack.zip"
        with zipfile.ZipFile(pack, "w") as z:
            z.writestr("pack.mcmeta", json.dumps({"pack": {"pack_format": 61}}))
            z.writestr("data/zion/function/hello.mcfunction", "say Hello")
        self.manifest["artifacts"] = [{"kind": "datapack", "source": "pack.zip", "filename": "room.zip", "sha256": d.digest(pack), "validation": {"datapack": True}}]
        self.creation()
        journal = d.deploy(self.runtime, self.manifest, self.root)
        self.assertTrue((self.runtime.server / "world/datapacks/room.zip").is_file())
        d.rollback(self.runtime, journal["id"])
        self.check_preserved()

    def test_manifest_failure_and_missing_compile_receipt_block_before_stop(self):
        self.validator.return_value = ["missing client artwork"]
        with self.assertRaisesRegex(d.DeployError, "Creation validation failed"):
            d.deploy(self.runtime, self.manifest, self.root)
        self.assertEqual(self.runtime.events, [])
        self.validator.return_value = []
        path = self.root / "creation.json"
        creation = json.loads(path.read_text())
        creation["evidence"] = []
        path.write_text(json.dumps(creation))
        self.manifest["creation_sha256"] = d.digest(path)
        with self.assertRaisesRegex(d.DeployError, "compile evidence"):
            d.deploy(self.runtime, self.manifest, self.root)

    def test_failed_start_restores_world_changed_by_new_mod(self):
        start = self.runtime.start
        attempts = 0

        def fail_first_start():
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                self.world.write_bytes(b"failed mod changed world")
                (self.world.parent / "new.mca").write_bytes(b"failed generation")
                raise d.DeployError("new mod crashed during world loading")
            return start()

        self.runtime.start = fail_first_start
        with self.assertRaisesRegex(d.DeployError, "previous tracked files restored"):
            d.deploy(self.runtime, self.manifest, self.root)
        self.check_preserved()
        self.assertFalse((self.world.parent / "new.mca").exists())

    def test_normal_rollback_preserves_later_player_progress(self):
        journal = d.deploy(self.runtime, self.manifest, self.root)
        self.world.write_bytes(b"Zion built a castle after deployment")
        d.rollback(self.runtime, journal["id"])
        self.assertEqual(self.world.read_bytes(), b"Zion built a castle after deployment")

    def test_open_client_blocks_without_explicit_graceful_close(self):
        self.runtime.client_processes = lambda: [{"pid": 800, "started": "test"}]
        with self.assertRaisesRegex(d.DeployError, "affected Minecraft client is open"):
            d.deploy(self.runtime, self.manifest, self.root)
        self.assertEqual(self.runtime.events, [])
        self.assertFalse((self.runtime.server / "mods/sword-2.jar").exists())

    def test_client_detection_uses_process_cwd_for_relative_or_default_game_dir(self):
        for launch in ("java --gameDir . --accessToken PRIVATE_TEST_VALUE", "java --launchTarget forgeclient --accessToken PRIVATE_TEST_VALUE"):
            def run(argv, **kwargs):
                if argv[:2] == ["ps", "-axo"]:
                    return SimpleNamespace(stdout="800 /jdk/bin/java\n", returncode=0)
                if argv[0] == "lsof":
                    return SimpleNamespace(stdout="p800\nfcwd\nn" + str(self.runtime.client.parent) + "\n", returncode=0)
                if argv[-1] == "args=":
                    return SimpleNamespace(stdout=launch, returncode=0)
                return SimpleNamespace(stdout="Mon Jan 1 12:00:00 2026\n", returncode=0)
            with patch.object(d.subprocess, "run", side_effect=run):
                found = d.Runtime.client_processes(self.runtime)
            self.assertEqual(found, [{"pid": 800, "started": "Mon Jan 1 12:00:00 2026"}])
            self.assertNotIn("PRIVATE_TEST_VALUE", json.dumps(found))

    def test_explicit_world_restore_rejects_changed_fingerprint(self):
        journal = d.deploy(self.runtime, self.manifest, self.root)
        self.runtime.stop()
        fingerprint = d.world_inventory(self.runtime)[2]
        self.world.write_bytes(b"changed after inspection")
        with self.assertRaisesRegex(d.DeployError, "World changed"):
            d.rollback(self.runtime, journal["id"], fingerprint)
        self.assertTrue((self.runtime.server / "mods/sword-2.jar").exists())
        self.assertEqual(self.world.read_bytes(), b"changed after inspection")

    def test_explicit_stopped_world_restore_is_separate_from_normal_rollback(self):
        journal = d.deploy(self.runtime, self.manifest, self.root)
        self.runtime.stop()
        self.world.write_bytes(b"deliberately discard this progress")
        fingerprint = d.world_inventory(self.runtime)[2]
        d.rollback(self.runtime, journal["id"], fingerprint)
        self.check_preserved()


if __name__ == "__main__":
    unittest.main()

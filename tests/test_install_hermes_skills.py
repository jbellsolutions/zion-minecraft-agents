import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("install_skills", ROOT / "tools/install_hermes_skills.py")
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def test_existing_command_name_is_not_shadowed(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory).resolve()
            existing = home / "skills/old-zion/SKILL.md"
            existing.parent.mkdir(parents=True)
            existing.write_text("---\nname: zion\ndescription: Original command\n---\nKeep me\n")
            with self.assertRaisesRegex(ValueError, "same command name"):
                installer.install(ROOT, home)
            self.assertIn("Keep me", existing.read_text())

    def test_additive_install_update_and_local_edit_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory).resolve()
            authority = home / "skills/gaming/minecraft-forge-authority/SKILL.md"
            authority.parent.mkdir(parents=True)
            authority.write_text("Learned live Minecraft patterns")
            installer.install(ROOT, home)
            installer.install(ROOT, home)
            self.assertEqual(authority.read_text(), "Learned live Minecraft patterns")
            skill = home / "skills/zion-supercharge/zion/SKILL.md"
            skill.write_text(skill.read_text() + "\nA new locally learned pattern\n")
            with self.assertRaisesRegex(ValueError, "Locally changed skill preserved"):
                installer.install(ROOT, home)
            self.assertIn("locally learned", skill.read_text())
            self.assertEqual(authority.read_text(), "Learned live Minecraft patterns")


if __name__ == "__main__":
    unittest.main()

"""Failure-oriented builder tests. All providers, artwork and receipts are fixtures."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asset_validation import decode_png, validate_png, validate_resource_tree
from tools.creation_manifest import TARGET, REQUIRED_EVIDENCE, file_sha256, validate_manifest
from tools.forge_asset_guard import validate as forge_validate
from tools.hermes_datapack_guard import validate as datapack_validate
from tools.zion_jobs import JobBusy, JobError, JobRunner, JobStore, file_lock


def png(size=64, opaque=False, palette=False, filter_type=0):
    """Tiny deterministic test silhouette; never used as production artwork."""
    def chunk(kind, payload):
        return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff)
    channels = 1 if palette else 4
    raw, previous = bytearray(), bytearray(size * channels)
    for y in range(size):
        row = bytearray()
        for x in range(size):
            visible = opaque or 0 < x < y < size - 1
            if palette:
                row.append(1 + (x % 2) if visible else 0)
            else:
                row.extend((x % 256, 100, 210, 255 if visible else 0))
        filtered = bytearray(row)
        for i, value in enumerate(row):
            left = row[i-channels] if i >= channels else 0
            above = previous[i]
            upper = previous[i-channels] if i >= channels else 0
            predictors = (0, left, above, (left + above)//2)
            if filter_type == 4:
                estimate = left + above - upper
                distances = (abs(estimate-left), abs(estimate-above), abs(estimate-upper))
                predictor = (left, above, upper)[distances.index(min(distances))]
            else:
                predictor = predictors[filter_type]
            filtered[i] = (value - predictor) & 255
        raw.extend(bytes([filter_type]) + filtered)
        previous = row
    content = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 3 if palette else 6, 0, 0, 0))
    if palette:
        content += chunk(b'PLTE', b'\0\0\0\xff\x80\0\x20\xff\xff') + chunk(b'tRNS', b'\0\xff\xff')
    return content + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def make_creation(root, *, complete=False, block=False):
    root.mkdir(parents=True, exist_ok=True)
    namespace, name = 'test_creation', 'chair' if block else 'shiny_sword'
    resources = root / 'source/src/main/resources'
    assets = resources / 'assets' / namespace
    icon = assets / 'textures/item' / (name + '.png')
    icon.parent.mkdir(parents=True)
    icon.write_bytes(png())
    model = assets / 'models' / ('block' if block else 'item') / (name + '.json')
    model_data = {'parent':'minecraft:item/generated', 'textures':{'layer0':f'{namespace}:item/{name}'}}
    if block:
        model_data = {'textures':{'wood':'minecraft:block/oak_planks'}, 'elements':[{
            'from':[2, 0, 2], 'to':[14, 8, 14], 'faces':{'up':{'texture':'#wood'}}}]}
        write_json(assets / 'blockstates' / (name + '.json'), {'variants':{'':{'model':f'{namespace}:block/{name}'}}})
    write_json(model, model_data)
    definition = assets / 'items' / (name + '.json')
    write_json(definition, {'model':{'type':'minecraft:model', 'model':f'{namespace}:{"block" if block else "item"}/{name}'}})
    write_json(resources / 'pack.mcmeta', {'pack':{'pack_format':46, 'description':'test fixture'}})
    (resources / 'META-INF').mkdir()
    (resources / 'META-INF/mods.toml').write_text('modLoader="javafml"\n[[mods]]\nmodId="test_creation"\n')
    # Structural archive fixture only; actual runtime proof is outside unit tests.
    (resources / 'Fixture.class').write_bytes(b'\xca\xfe\xba\xbe\0\0\0A')
    artifact = root / 'fixture.jar'
    with zipfile.ZipFile(artifact, 'w') as jar:
        for path in resources.rglob('*'):
            if path.is_file():
                jar.write(path, path.relative_to(resources))
    thumbnail = root / 'thumbnail.png'
    thumbnail.write_bytes(png())
    def record(path, kind, capability=None):
        data = {'path':path.relative_to(root).as_posix(), 'kind':kind, 'sha256':file_sha256(path)}
        if capability:
            data['capability_id'] = capability
        return data
    asset_records = [record(thumbnail, 'thumbnail'), record(model, 'model', name), record(definition, 'item_definition', name)]
    if not block:
        asset_records.append(record(icon, 'inventory_icon', name))
    data = {'schema_version':1, 'id':'test_creation', 'name':'Test Creation', 'request':'Build a shiny sword', 'target':TARGET,
            'capabilities':[{'id':name, 'kind':'block' if block else 'item', 'description':'Test content', 'registry_id':f'{namespace}:{name}', 'requires_geometry':block}],
            'assets':asset_records, 'commands':[{'literal':f'/zion give {name}', 'capability_id':name, 'action':'give'}],
            'artifacts':[record(artifact, 'jar')], 'evidence':[]}
    if complete:
        for check in REQUIRED_EVIDENCE:
            report = root / 'evidence' / (check + '.txt')
            report.parent.mkdir(exist_ok=True)
            report.write_text('Simulated test receipt: ' + check)
            data['evidence'].append({'check':check, 'status':'passed', 'path':report.relative_to(root).as_posix(),
                                     'sha256':file_sha256(report), 'artifact_sha256':file_sha256(artifact)})
    manifest = root / 'creation.json'
    write_json(manifest, data)
    return manifest, data


def reviewer(choice='supported'):
    return lambda **kwargs: {'choice':choice, 'advisory':True}


class AssetTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_decodes_palette_and_all_filters(self):
        for palette in (False, True):
            for filter_type in range(5):
                image = decode_png(png(palette=palette, filter_type=filter_type))
                self.assertTrue(image['transparent'])
                self.assertGreater(image['visible_colors'], 1)

    def test_header_only_corrupt_pixels_and_opaque_icons_fail(self):
        path = self.root / 'icon.png'
        for content in (png()[:33], png()[:-7], png()[:-13] + b'broken ending', png(opaque=True)):
            path.write_bytes(content)
            self.assertTrue(validate_png(path, inventory=True, release=True))
        path.write_bytes(png(32))
        self.assertIn('64x64', ' '.join(validate_png(path, inventory=True, release=True)))
        path.write_bytes(png())
        self.assertEqual([], validate_png(path, inventory=True, release=True))

    def test_model_graph_accepts_vanilla_and_rejects_missing_alias_cycles(self):
        path = self.root / 'assets/test/models/block/chair.json'
        write_json(path, {'textures':{'all':'minecraft:block/oak_planks'}, 'elements':[{'from':[1,0,1], 'to':[15,8,15], 'faces':{'up':{'texture':'#all'}}}]})
        self.assertEqual([], validate_resource_tree(self.root))
        write_json(path, {'parent':'test:block/chair', 'textures':{'all':'#other', 'other':'#all'}})
        self.assertIn('cyclic', ' '.join(validate_resource_tree(self.root)))
        write_json(path, {'parent':'test:block/absent'})
        self.assertIn('missing referenced models', ' '.join(validate_resource_tree(self.root)))

    def test_metadata_fix_never_creates_missing_art(self):
        (self.root / 'gradle.properties').write_text('minecraft_version=1.21.4\nmod_id=test\n')
        source = self.root / 'src/main/java/Test.java'
        source.parent.mkdir(parents=True)
        source.write_text('ITEMS.register("sword", anything);')
        issues, fixes = forge_validate(self.root, fix=True)
        self.assertTrue(fixes)
        self.assertIn('missing referenced textures', ' '.join(issues))
        self.assertEqual([], list(self.root.rglob('*.png')))
        definition = self.root / 'src/main/resources/assets/test/items/sword.json'
        self.assertTrue(definition.is_file())

    def test_multi_mod_requires_explicit_namespace_before_fix(self):
        path = self.root / 'src/main/resources/META-INF/mods.toml'
        write_json(self.root / 'unused.json', {})
        path.parent.mkdir(parents=True)
        path.write_text('[[mods]]\nmodId="builder"\n[[mods]]\nmodId="content"\n')
        with self.assertRaisesRegex(SystemExit, 'Multiple mod namespaces'):
            forge_validate(self.root, fix=True)
        self.assertFalse((self.root / 'src/main/resources/assets').exists())

    def test_datapack_singular_paths_and_function_refs(self):
        write_json(self.root / 'pack.mcmeta', {'pack':{'pack_format':61}})
        functions = self.root / 'data/test/function'
        functions.mkdir(parents=True)
        function = functions / 'load.mcfunction'
        function.write_text('say ready\n')
        self.assertEqual([], datapack_validate(self.root, False)[0])
        function.write_text('execute as @a run function test:missing\n')
        self.assertIn('missing referenced function', ' '.join(datapack_validate(self.root, False)[0]))
        function.write_text('/say invalid\nmispelled command\n')
        self.assertIn('unknown command root', ' '.join(datapack_validate(self.root, False)[0]))
        functions.rename(functions.with_name('functions'))
        self.assertIn('singular', ' '.join(datapack_validate(self.root, False)[0]))


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.manifest, self.data = make_creation(self.root)

    def test_valid_build_remains_missing_runtime_evidence(self):
        self.assertEqual([], validate_manifest(self.manifest))
        self.assertIn('missing passed evidence', ' '.join(validate_manifest(self.manifest, True)))

    def test_modeled_furniture_does_not_need_redundant_png(self):
        manifest, data = make_creation(self.root / 'furniture', block=True)
        self.assertEqual([], validate_manifest(manifest))

    def test_empty_commands_tampering_and_path_escape_fail(self):
        self.data['commands'] = []
        write_json(self.manifest, self.data)
        self.assertIn('slash command', ' '.join(validate_manifest(self.manifest)))
        self.data['artifacts'][0]['sha256'] = '0' * 64
        write_json(self.manifest, self.data)
        self.assertIn('SHA-256 mismatch', ' '.join(validate_manifest(self.manifest)))
        self.data['artifacts'][0]['path'] = '../outside.jar'
        write_json(self.manifest, self.data)
        self.assertIn('traverse', ' '.join(validate_manifest(self.manifest)))

    def test_passed_receipt_requires_bound_file(self):
        self.data['evidence'] = [{'check':'compile', 'status':'passed', 'artifact_sha256':'1' * 64}]
        write_json(self.manifest, self.data)
        issues = ' '.join(validate_manifest(self.manifest))
        self.assertIn('relative paths', issues)
        self.assertIn('current artifact', issues)

    def test_manifests_cannot_claim_different_icons_than_jar(self):
        asset = self.data['assets'][-1]
        path = self.root / asset['path']
        path.write_bytes(png(filter_type=1))
        asset['sha256'] = file_sha256(path)
        write_json(self.manifest, self.data)
        self.assertIn('does not match a packaged JAR', ' '.join(validate_manifest(self.manifest)))

    def test_registered_capability_requires_packaged_item_definition(self):
        self.data['capabilities'][0]['registry_id'] = 'test_creation:nonexistent'
        write_json(self.manifest, self.data)
        self.assertIn('built JAR is missing', ' '.join(validate_manifest(self.manifest)))

    def test_duplicate_compile_receipts_allowed_for_distinct_artifacts(self):
        other = self.root / 'second.jar'
        shutil.copy(self.root / 'fixture.jar', other)
        with zipfile.ZipFile(other, 'a') as archive:
            archive.writestr('different.txt', 'second artifact')
        report = self.root / 'compile.txt'
        report.write_text('Test fixture compilation receipt')
        self.data['artifacts'].append({'path':'second.jar', 'kind':'jar', 'sha256':file_sha256(other)})
        for artifact in self.data['artifacts']:
            self.data['evidence'].append({'check':'compile', 'status':'passed', 'path':'compile.txt',
                                         'sha256':file_sha256(report), 'artifact_sha256':artifact['sha256']})
        write_json(self.manifest, self.data)
        self.assertEqual([], validate_manifest(self.manifest))

    def test_malformed_values_return_issues_instead_of_crashing(self):
        self.data['commands'][0]['capability_id'] = ['bad']
        write_json(self.manifest, self.data)
        self.assertTrue(validate_manifest(self.manifest))


class JobTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.store = JobStore(self.root / 'jobs')

    def runner(self, script, **kwargs):
        return JobRunner(self.store, [sys.executable, '-c', script], poll_interval=.01, reviewer=reviewer(), **kwargs)

    def copy_provider(self, fixture):
        return "import shutil,sys; shutil.copytree(" + repr(str(fixture)) + ",sys.argv[sys.argv.index('--output-dir')+1],dirs_exist_ok=True)"

    def test_exit_zero_without_artifact_is_failed_and_durable(self):
        job = self.store.create('Build a shiny sword')
        result = self.runner('print("done")').run(job['id'])
        self.assertEqual('failed', result['status'])
        self.assertIn('did not produce creation.json', result['error'])
        self.assertEqual(result, JobStore(self.store.root).get(job['id']))

    def test_bounded_retry_keeps_errors_and_attempt_directories(self):
        job = self.store.create('Build a shiny sword')
        runner = self.runner('import sys; print("compile failed"); sys.exit(7)')
        for attempt in range(1, 4):
            result = runner.run(job['id'], retry=attempt > 1)
            self.assertEqual(attempt, result['attempts'])
            self.assertIn('status 7', result['error'])
        with self.assertRaisesRegex(JobError, 'three-attempt'):
            runner.run(job['id'], retry=True)
        request = json.loads((self.store.directory(job['id']) / 'attempt-2/request.json').read_text())
        self.assertIn('compile failed', request['previous_error'])

    def test_timeout_does_not_succeed(self):
        job = self.store.create('Build a shiny sword')
        result = self.runner('import time; time.sleep(15)', timeout=.05).run(job['id'])
        self.assertEqual('failed', result['status'])
        self.assertIn('timed out', result['error'])

    def test_cancel_running_job_and_prevent_duplicate_workers(self):
        job = self.store.create('Build a shiny sword')
        runner = self.runner('import time; time.sleep(15)')
        worker = threading.Thread(target=runner.run, args=(job['id'],))
        worker.start()
        deadline = time.monotonic() + 3
        while self.store.get(job['id'], recover=False)['status'] != 'running' and time.monotonic() < deadline:
            time.sleep(.01)
        with self.assertRaises(JobBusy):
            runner.run(job['id'])
        self.store.cancel(job['id'])
        worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertEqual('cancelled', self.store.get(job['id'])['status'])

    def test_stale_worker_state_recovers_without_restarting_job(self):
        job = self.store.create('Build a shiny sword')
        self.store.update(job['id'], status='running')
        self.assertEqual('interrupted', self.store.get(job['id'])['status'])
        with file_lock(self.store.directory(job['id']) / 'run.lock'):
            self.store.update(job['id'], status='running')
            self.assertEqual('running', self.store.get(job['id'])['status'])

    def test_partial_evidence_is_pending_and_resume_reuses_build(self):
        fixture = self.root / 'fixture'
        make_creation(fixture)
        job = self.store.create('Build a shiny sword')
        runner = self.runner(self.copy_provider(fixture))
        result = runner.run(job['id'])
        self.assertEqual('awaiting_verification', result['status'])
        self.assertIn('client_render', result['pending_checks'])
        result = runner.run(job['id'], resume=True)
        self.assertEqual(1, result['attempts'])
        self.assertEqual('awaiting_verification', result['status'])

    def test_jev_outcomes_never_replace_runtime_checks(self):
        for choice, complete, expected in [('supported', False, 'awaiting_verification'),
                                            ('supported', True, 'succeeded'), ('unavailable', True, 'succeeded'),
                                            ('insufficient', True, 'awaiting_review'), ('contradicted', True, 'failed')]:
            fixture = self.root / (choice + str(complete))
            make_creation(fixture, complete=complete)
            job = self.store.create('Build a shiny sword')
            runner = JobRunner(self.store, [sys.executable, '-c', self.copy_provider(fixture)], reviewer=reviewer(choice), poll_interval=.01)
            result = runner.run(job['id'])
            self.assertEqual(expected, result['status'])
            self.assertEqual(choice, result['semantic_review']['choice'])
            if choice == 'unavailable':
                self.assertIn('unavailable', result['text'])
            if expected == 'succeeded':
                self.assertIn('No deployment', result['text'])

    def test_provider_logs_redact_environment_secrets(self):
        secret = 'unit-test-secret-value-123'
        job = self.store.create('Build a shiny sword')
        with patch.dict(os.environ, {'TEST_API_KEY':secret}):
            result = self.runner('import os,sys; print(os.environ["TEST_API_KEY"]); sys.exit(1)').run(job['id'])
        self.assertNotIn(secret, json.dumps(result))
        log = self.store.directory(job['id']) / 'attempt-1/provider.log'
        self.assertIn('[redacted]', log.read_text())
        self.assertNotIn(secret, log.read_text())

    def test_ui_uses_same_durable_status(self):
        spec = importlib.util.spec_from_file_location('zion_ui', ROOT / 'ui/server.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        service = module.BuilderService(self.store, self.runner('print("not actually built")'))
        job = service.start(request='Build a shiny sword')
        service.worker.join(3)
        status = service.status(job['id'])
        self.assertEqual('failed', status['status'])
        self.assertTrue(status['terminal'])
        self.assertNotIn('error', status)


if __name__ == '__main__':
    unittest.main()

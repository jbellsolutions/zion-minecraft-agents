"""The public library exposes validated creations, never arbitrary job paths."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
from test_reliability import make_creation
from tools.creation_manifest import file_sha256
from tools.zion_jobs import JobError, JobStore

spec = importlib.util.spec_from_file_location('zion_library_ui', ROOT / 'ui/server.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.store = JobStore(self.root / 'jobs')
        self.legacy = self.root / 'library.json'
        self.installed = self.root / 'installed.json'
        self.service = server.BuilderService(self.store, legacy_path=self.legacy, installed_path=self.installed)

    def creation(self, complete=False):
        job = self.store.create('Build a shiny sword')
        output = self.store.directory(job['id']) / 'attempt-1/output'
        manifest, data = make_creation(output, complete=complete)
        self.store.update(job['id'], status='succeeded' if complete else 'awaiting_verification', manifest_path=str(manifest))
        return job, manifest, data

    def test_library_comes_from_saved_manifests_and_preserves_pending_status(self):
        job, manifest, data = self.creation()
        card = self.service.library()['mods'][0]
        self.assertEqual('Test Creation', card['name'])
        self.assertEqual('needs_checks', card['status'])
        self.assertEqual(['/zion give shiny_sword'], card['commands'])
        self.assertEqual('/jobs/' + job['id'] + '/icon', card['icon'])
        self.assertEqual((manifest.parent / 'thumbnail.png').read_bytes(), self.service.icon(job['id']))
        self.assertNotIn('manifest_path', card)

    def test_complete_job_alone_never_claims_installation(self):
        self.creation(complete=True)
        self.assertEqual('verified', self.service.library()['mods'][0]['status'])

    def test_tampered_artifact_and_icon_are_not_published(self):
        job, manifest, data = self.creation()
        (manifest.parent / 'fixture.jar').write_bytes(b'changed build')
        self.assertEqual([], self.service.library()['mods'])
        with self.assertRaises(JobError):
            self.service.icon(job['id'])

    def test_manifest_and_icon_traversal_are_rejected(self):
        job = self.store.create('Build a shiny sword')
        outside, data = make_creation(self.root / 'outside')
        self.store.update(job['id'], manifest_path=str(outside), status='succeeded')
        self.assertEqual([], self.service.library()['mods'])
        with self.assertRaisesRegex(JobError, 'leaves its job'):
            self.service.icon(job['id'])
        with self.assertRaises(JobError):
            self.service.icon('../outside')
        job2, manifest, data = self.creation()
        data['assets'][0]['path'] = '../../../../outside/thumbnail.png'
        manifest.write_text(json.dumps(data))
        with self.assertRaises(JobError):
            self.service.icon(job2['id'])

    def test_installed_badge_requires_bound_receipt_and_both_current_hashes(self):
        job, manifest, data = self.creation(complete=True)
        artifact = manifest.parent / 'fixture.jar'
        server_path, client_path = self.root / 'server.jar', self.root / 'client.jar'
        shutil.copyfile(artifact, server_path)
        shutil.copyfile(artifact, client_path)
        receipt = {'schema_version':1, 'installations':[{
            'creation_id':data['id'], 'creation_sha256':file_sha256(manifest), 'status':'deployed', 'transaction_id':'test-transaction',
            'artifacts':[{'sha256':file_sha256(artifact), 'server_path':str(server_path), 'client_path':str(client_path)}]}]}
        self.installed.write_text(json.dumps(receipt))
        self.assertEqual('installed', self.service.library()['mods'][0]['status'])
        client_path.write_bytes(b'older client artifact')
        self.assertEqual('verified', self.service.library()['mods'][0]['status'])
        shutil.copyfile(artifact, client_path)
        receipt['installations'][0]['creation_sha256'] = '0'*64
        self.installed.write_text(json.dumps(receipt))
        self.assertEqual('verified', self.service.library()['mods'][0]['status'])

    def test_legacy_active_is_unverified_and_does_not_duplicate_valid_jobs(self):
        self.legacy.write_text(json.dumps({'mods':[
            {'id':'test_creation', 'name':'Old duplicate', 'status':'active'},
            {'id':'old_mod', 'name':'Old saved creation', 'status':'active'}]}))
        self.creation(complete=True)
        cards = self.service.library()['mods']
        self.assertEqual(2, len(cards))
        self.assertEqual('Test Creation', cards[0]['name'])
        self.assertEqual('legacy', cards[1]['status'])


if __name__ == '__main__':
    unittest.main()

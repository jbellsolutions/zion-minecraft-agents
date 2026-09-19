"""Release packaging rejects stale proof and preserves unrelated output files."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.creation_manifest import file_sha256
from tools.package_showcase import assemble, copy_runtime_receipt, package


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.proof = self.root / 'input'
        self.proof.mkdir()
        self.output = self.root / 'output'
        self.output.mkdir()

    def test_runtime_receipt_must_identify_current_artifact(self):
        receipt = self.proof / 'client_join.json'
        receipt.write_text(json.dumps({'check':'client_join', 'status':'passed', 'artifact_sha256':'a'*64}))
        with self.assertRaisesRegex(ValueError, 'different artifact'):
            copy_runtime_receipt(receipt, 'client_join', self.output, 'b'*64)
        self.assertEqual([], list(self.output.iterdir()))

    def test_missing_or_changed_proof_file_blocks_pass(self):
        receipt = self.proof / 'client_render.json'
        data = {'check':'client_render', 'status':'passed', 'artifact_sha256':'a'*64,
                'proof_files':[{'path':'screen.png', 'sha256':'0'*64}]}
        receipt.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'missing or its hash changed'):
            copy_runtime_receipt(receipt, 'client_render', self.output, 'a'*64)
        data['proof_files'][0]['path'] = '../outside.png'
        receipt.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'traverse'):
            copy_runtime_receipt(receipt, 'client_render', self.output, 'a'*64)

    def test_real_receipt_and_companion_file_are_copied_unchanged(self):
        log = self.proof / 'join.log'
        log.write_text('Test fixture connection evidence')
        receipt = self.proof / 'client_join.json'
        receipt.write_text(json.dumps({'check':'client_join', 'status':'passed', 'artifact_sha256':'a'*64,
                                      'proof_files':[{'path':'join.log', 'sha256':file_sha256(log)}]}))
        record = copy_runtime_receipt(receipt, 'client_join', self.output, 'a'*64)
        self.assertEqual(file_sha256(receipt), record['sha256'])
        self.assertEqual(log.read_bytes(), (self.output / 'evidence/runtime/client_join/join.log').read_bytes())

    def test_stale_build_receipt_cannot_package_new_jar(self):
        artifact = self.root / 'release.jar'
        artifact.write_bytes(b'new-build-test-fixture')
        project = self.root / 'project'
        (project / 'verification').mkdir(parents=True)
        (project / 'verification/build-and-gameplay.json').write_text(json.dumps({'sha256':'0'*64}))
        with self.assertRaisesRegex(ValueError, 'SHA-256 does not match'):
            assemble(self.output, project, artifact)
        self.assertEqual([], list(self.output.iterdir()))

    def test_nonrelease_output_directory_is_preserved(self):
        important = self.output / 'keep.txt'
        important.write_text('existing work')
        artifact = self.root / 'release.jar'
        artifact.write_bytes(b'test')
        with self.assertRaisesRegex(ValueError, 'non-release'):
            package(self.output, project=self.root, artifact=artifact)
        self.assertEqual('existing work', important.read_text())


if __name__ == '__main__':
    unittest.main()

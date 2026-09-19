#!/usr/bin/env python3
"""Package the tested showcase without inventing runtime proof or touching a game."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile

try:
    from .creation_manifest import TARGET, REQUIRED_EVIDENCE, confined_path, file_sha256, missing_evidence, validate_manifest
except ImportError:
    from creation_manifest import TARGET, REQUIRED_EVIDENCE, confined_path, file_sha256, missing_evidence, validate_manifest

ROOT = Path(__file__).resolve().parents[1]
REQUEST = 'Can you make a rainbow motorcycle that goes 1000 mph with a yoda driving it?'
FURNITURE = {
    'fridge': 'A modeled refrigerator with persistent inventory storage.',
    'grill': 'A shaped grill that cooks ingredients using fuel.',
    'stove': 'A modeled stove that cooks ingredients using fuel.',
    'oven': 'A modeled oven with persistent cooking progress.',
    'bookshelf': 'A shaped bookshelf with persistent inventory storage.',
    'chair': 'A modeled chair that the player can sit on and dismount.',
    'sofa': 'A modeled sofa with a usable seat.',
    'sink': 'A shaped sink with a water interaction.',
    'toilet': 'A modeled toilet with a usable seat and flush interaction.',
    'shower': 'A shaped shower with water particles and sound.',
}
ROOMS = ('bedroom', 'kitchen', 'bathroom', 'sitting_room', 'chill_room', 'house')


def read_json(path):
    value = json.loads(Path(path).read_text())
    if not isinstance(value, dict):
        raise ValueError(f'{path}: expected a JSON object')
    return value


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def copy_file(source, destination):
    if source.is_symlink() or not source.is_file():
        raise ValueError(f'Expected a regular input file: {source}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def evidence_record(check, report, root, artifact_hash, status='passed'):
    value = {'check': check, 'status': status, 'artifact_sha256': artifact_hash}
    if report is not None:
        value.update(path=report.relative_to(root).as_posix(), sha256=file_sha256(report))
    return value


def copy_runtime_receipt(path, check, root, artifact_hash):
    """Only explicit, matching receipts can promote an optional runtime gate."""
    value = read_json(path)
    if value.get('check') != check or value.get('status') not in ('passed', 'pending', 'failed'):
        raise ValueError(f'{path}: expected explicit check={check} and a verification status')
    if value.get('artifact_sha256') != artifact_hash:
        raise ValueError(f'{path}: runtime evidence belongs to a different artifact')
    proofs = value.get('proof_files', [])
    if not isinstance(proofs, list):
        raise ValueError(f'{path}: proof_files must be an array')
    destination = root / 'evidence/runtime' / check / path.name
    for proof in proofs:
        if not isinstance(proof, dict):
            raise ValueError(f'{path}: invalid proof file')
        source = confined_path(path.parent, proof.get('path'))
        if not source.is_file() or file_sha256(source) != proof.get('sha256'):
            raise ValueError(f'{path}: proof file is missing or its hash changed')
        target = confined_path(destination.parent, proof['path'])
        if target == destination:
            raise ValueError(f'{path}: a proof file cannot replace its receipt')
        copy_file(source, target)
    copy_file(path, destination)
    return evidence_record(check, destination, root, artifact_hash, value['status'])


def assemble(root, project, artifact, evidence_dir=None, thumbnail=None, request=REQUEST):
    artifact_hash = file_sha256(artifact)
    report_path = project / 'verification/build-and-gameplay.json'
    report = read_json(report_path)
    if report.get('sha256') != artifact_hash:
        raise ValueError('Build/gameplay receipt SHA-256 does not match the selected JAR; rebuild and rerun the tests first')
    if any(report.get(field) != TARGET[field] for field in ('minecraft', 'forge', 'java')):
        raise ValueError('Build receipt does not match the pinned Minecraft/Forge/Java target')
    if report.get('compile') != 'passed' or report.get('asset_guard') != 'passed':
        raise ValueError('Passed compilation and asset-guard receipts are required')
    build_log = project / 'verification/release-build.log'
    if not build_log.is_file() or 'BUILD SUCCESSFUL' not in build_log.read_text(errors='replace'):
        raise ValueError('The successful release compilation log is missing')
    game_tests = report.get('game_tests', {})
    if not isinstance(game_tests, dict) or game_tests.get('failed') != 0 or not isinstance(game_tests.get('passed'), int) or game_tests['passed'] <= 0:
        raise ValueError('A successful gameplay test receipt is required')
    game_log = confined_path(report_path.parent, game_tests.get('log'))
    if not game_log.is_file() or f"All {game_tests['passed']} required tests passed" not in game_log.read_text(errors='replace'):
        raise ValueError('The matching successful gameplay log is missing')

    resources = project / 'src/main/resources'
    for source in sorted(resources.rglob('*')):
        if source.is_symlink():
            raise ValueError(f'Source resource symlink is not permitted: {source}')
        if source.is_file():
            copy_file(source, root / 'resources' / source.relative_to(resources))
    artifact_target = root / 'artifacts' / artifact.name
    copy_file(artifact, artifact_target)
    if file_sha256(artifact_target) != artifact_hash:
        raise ValueError('The artifact changed while packaging')
    thumbnail = thumbnail or resources / 'assets/zion_showcase/textures/item/rainbow_motorcycle.png'
    thumbnail_target = root / 'preview/showcase.png'
    copy_file(thumbnail, thumbnail_target)
    build_report = root / 'evidence/build-and-gameplay.json'
    copy_file(report_path, build_report)
    copy_file(build_log, root / 'evidence/release-build.log')
    copy_file(game_log, confined_path(root / 'evidence', game_tests['log']))

    capabilities = [
        {'id': 'shiny_sword', 'kind': 'item', 'registry_id': 'zion_showcase:shiny_sword',
         'description': 'A usable shiny sword with a distinctive transparent inventory icon and enchantment glint.'},
        {'id': 'rainbow_motorcycle', 'kind': 'entity', 'registry_id': 'zion_showcase:rainbow_motorcycle',
         'description': 'A modeled rideable rainbow motorcycle with a visible Yoda driver, steering, braking, swept collision, persistence, and turbo targeting 1,000 mph on a clear loaded road.'},
    ]
    capabilities.extend({'id': name, 'kind': 'block', 'registry_id': 'zion_showcase:' + name,
                         'description': description, 'requires_geometry': True} for name, description in FURNITURE.items())
    capabilities.extend({'id': name, 'kind': 'structure' if name == 'house' else 'room',
                         'description': 'A furnished ' + name.replace('_', ' ') + ' with safe placement preview, bounded building, location tracking, and persistent undo.'} for name in ROOMS)
    physical = {item['id'] for item in capabilities if item['kind'] in ('item', 'entity', 'block')}
    assets = []
    def asset(path, kind, capability=None):
        value = {'path': path.relative_to(root).as_posix(), 'kind': kind, 'sha256': file_sha256(path)}
        if capability:
            value['capability_id'] = capability
        assets.append(value)
    asset(thumbnail_target, 'thumbnail')
    for path in sorted((root / 'resources/assets/zion_showcase').rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(root / 'resources/assets/zion_showcase')
        section = relative.parts[0]
        kind = {'models': 'model', 'items': 'item_definition', 'blockstates': 'blockstate'}.get(section)
        if section == 'textures' and path.suffix == '.png':
            kind = 'inventory_icon' if relative.parts[1] == 'item' else 'texture'
        if kind:
            asset(path, kind, path.stem if path.stem in physical else None)
    commands = [{'literal': '/zion give ' + name, 'capability_id': name, 'action': 'give'} for name in sorted(physical)]
    commands.append({'literal': '/zion spawn rainbow_motorcycle', 'capability_id': 'rainbow_motorcycle', 'action': 'spawn'})
    commands.extend({'literal': '/zion place ' + name, 'capability_id': name, 'action': 'place'} for name in ROOMS)
    evidence = [evidence_record(check, build_report, root, artifact_hash) for check in ('compile', 'gameplay')]
    for check in sorted(REQUIRED_EVIDENCE - {'compile', 'gameplay'}):
        receipt = Path(evidence_dir) / (check + '.json') if evidence_dir else None
        evidence.append(copy_runtime_receipt(receipt, check, root, artifact_hash) if receipt and receipt.is_file()
                        else evidence_record(check, None, root, artifact_hash, 'pending'))
    creation = {'schema_version': 1, 'id': 'zion_showcase', 'name': 'Zion Supercharged Showcase',
                'request': request, 'target': TARGET, 'capabilities': capabilities, 'assets': assets,
                'commands': commands, 'artifacts': [{'path': artifact_target.relative_to(root).as_posix(), 'kind': 'jar', 'sha256': artifact_hash}],
                'evidence': evidence}
    manifest = root / 'creation.json'
    write_json(manifest, creation)
    issues = validate_manifest(manifest)
    if issues:
        raise ValueError('Release validation failed: ' + '; '.join(issues))
    write_json(root / 'deployment.json', {'schema_version': 1, 'job_id': 'zion_showcase', 'minecraft': TARGET['minecraft'],
               'forge': TARGET['forge'], 'creation_manifest': 'creation.json', 'creation_sha256': file_sha256(manifest),
               'artifacts': [{'kind': 'mod', 'source': artifact_target.relative_to(root).as_posix(),
                              'filename': artifact.name, 'sha256': artifact_hash, 'replaces': []}]})
    write_json(root / '.zion-release.json', {'schema_version': 1, 'kind': 'zion_showcase_release'})
    return {'artifact_sha256': artifact_hash, 'pending_checks': missing_evidence(creation), 'capabilities': len(capabilities)}


def package(output, project=None, artifact=None, evidence_dir=None, thumbnail=None, request=REQUEST):
    project = Path(project or ROOT / 'mods/zion-supercharge').resolve()
    if artifact is None:
        artifacts = sorted((project / 'build/libs').glob('*.jar'))
        artifacts = [path for path in artifacts if not any(label in path.stem for label in ('sources', 'javadoc', 'test'))]
        if len(artifacts) != 1:
            raise ValueError('Select --artifact explicitly: expected exactly one release JAR')
        artifact = artifacts[0]
    artifact = Path(artifact).resolve()
    output = Path(output).absolute()
    if output.is_symlink():
        raise ValueError('Release output cannot be a symlink')
    if output.exists():
        marker = output / '.zion-release.json'
        if not marker.is_file() or read_json(marker) != {'schema_version': 1, 'kind': 'zion_showcase_release'}:
            raise ValueError('Refusing to overwrite a non-release output directory')
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.showcase-stage-', dir=output.parent))
    backup = None
    try:
        result = assemble(staging, project, artifact, evidence_dir, thumbnail, request)
        if output.exists():
            backup = Path(tempfile.mkdtemp(prefix='.showcase-previous-', dir=output.parent)) / 'release'
            os.replace(output, backup)
        try:
            os.replace(staging, output)
        except OSError:
            if backup:
                os.replace(backup, output)
            raise
        result.update(output=str(output), creation_manifest=str(output / 'creation.json'), deployment_manifest=str(output / 'deployment.json'))
        if backup:
            result['previous_bundle'] = str(backup)
        return result
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / '.zion/release')
    parser.add_argument('--project', type=Path)
    parser.add_argument('--artifact', type=Path)
    parser.add_argument('--evidence-dir', type=Path)
    parser.add_argument('--thumbnail', type=Path)
    parser.add_argument('--request-file', type=Path, help='plain text request; retained verbatim')
    args = parser.parse_args()
    try:
        request = args.request_file.read_text() if args.request_file else REQUEST
        result = package(args.output, args.project, args.artifact, args.evidence_dir, args.thumbnail, request)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({'error': str(error)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Produce a reproducible source-and-tested-release ZIP, excluding private state."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import zipfile

from creation_manifest import validate_manifest

ROOT = Path(__file__).resolve().parents[1]


def make_package(output):
    release = ROOT / '.zion/release'
    issues = validate_manifest(release / 'creation.json', require_evidence=True)
    if issues:
        raise ValueError('Release is not fully verified: ' + '; '.join(issues))
    subprocess.run(['python3', str(ROOT / 'tools/check_public_secrets.py')], cwd=ROOT, check=True)
    result = subprocess.run(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT, capture_output=True, check=True)
    files = {}
    for name in set(result.stdout.decode().split('\0')) - {''}:
        path = ROOT / name
        if Path(name).parts[0] == 'releases' or path.is_symlink() or not path.is_file():
            continue
        if path.name.startswith('.env') and path.name != '.env.example':
            raise ValueError('Private environment file cannot be packaged')
        files[name] = path
    for path in release.rglob('*'):
        if path.is_symlink():
            raise ValueError('Release symlinks are not allowed')
        if path.is_file():
            files['release/' + path.relative_to(release).as_posix()] = path
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, path in sorted(files.items()):
            info = zipfile.ZipInfo('zion-supercharge/' + name, (2026, 9, 19, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100000 | (path.stat().st_mode & 0o777)) << 16
            archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(output) as archive:
        if archive.testzip():
            raise ValueError('Update ZIP failed its CRC check')
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.zip.sha256').write_text(digest + '  ' + output.name + '\n')
    print(f'{output}: {len(files)} files, sha256 {digest}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'releases/zion-supercharge-update-1.1.0.zip')
    make_package(parser.parse_args().output)

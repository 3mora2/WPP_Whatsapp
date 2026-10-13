"""Validate release provenance and package payloads without importing the package.

Runs on Python 3.9+; uses only the standard library. Never extracts archives.
"""
import argparse
import email
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
import zipfile


PACKAGE = 'WPP_Whatsapp'
ASSETS = ('js_lib/wapi.js', 'js_lib/wppconnect-wa.js', 'js_lib/message_compat.js')
SUFFIXES = {'.py', '.js', '.json', '.md', '.typed'}


def version(source):
    text = (Path(source) / 'pyproject.toml').read_text(encoding='utf-8')
    section = re.search(r'(?ms)^\[project\]\s*(.*?)(?=^\[|\Z)', text)
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', section[1] if section else '')
    if not match:
        raise ValueError('A static project.version is required')
    return match[1]


def request_json(url, token=None):
    headers = {'Accept': 'application/json', 'User-Agent': 'WPP-Whatsapp-release-check'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return json.load(response)


def plan(source):
    event_name = os.environ['GITHUB_EVENT_NAME']
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text(encoding='utf-8'))
    publish = event_name in ('release', 'workflow_dispatch')
    ref = os.environ['GITHUB_SHA']
    tag = ''
    if publish:
        tag = (event.get('release', {}).get('tag_name') if event_name == 'release'
               else event.get('inputs', {}).get('release_tag', ''))
        if not isinstance(tag, str) or not re.fullmatch(r'v?\d+\.\d+\.\d+(?:(?:a|b|rc)\d+|\.post\d+)?', tag):
            raise ValueError('release_tag must be a version tag, for example v1.2.0')
        repository = os.environ['GITHUB_REPOSITORY']
        release = request_json(f'https://api.github.com/repos/{repository}/releases/tags/{quote(tag, safe="")}', os.getenv('GH_TOKEN'))
        if release.get('draft') or not release.get('published_at') or release.get('tag_name') != tag:
            raise ValueError('Only an already published GitHub release can be deployed')
        ref = subprocess.check_output(['git', 'rev-parse', '--verify', f'refs/tags/{tag}^{{commit}}'], cwd=source, text=True).strip()
        metadata = subprocess.check_output(['git', 'show', f'{ref}:pyproject.toml'], cwd=source, text=True)
        section = re.search(r'(?ms)^\[project\]\s*(.*?)(?=^\[|\Z)', metadata)
        match = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', section[1] if section else '')
        if not match or match[1] != tag.removeprefix('v'):
            raise ValueError('Release tag does not match project.version at the tagged commit')
    result = {'ref': ref, 'publish': str(publish).lower(), 'tag': tag}
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as stream:
            stream.write(''.join(f'{key}={value}\n' for key, value in result.items()))
    print(json.dumps(result))
    return result


def archive_files(path_or_bytes, wheel):
    target = io.BytesIO(path_or_bytes) if isinstance(path_or_bytes, bytes) else path_or_bytes
    if wheel:
        with zipfile.ZipFile(target) as archive:
            members = [(entry.filename, archive.read(entry)) for entry in archive.infolist() if not entry.is_dir()]
    else:
        with tarfile.open(fileobj=target, mode='r:gz') if isinstance(target, io.BytesIO) else tarfile.open(target, 'r:gz') as archive:
            members = [(entry.name, archive.extractfile(entry).read()) for entry in archive.getmembers() if entry.isfile()]
    files = {}
    for name, contents in members:
        parts = PurePosixPath(name).parts
        if not parts or name.startswith('/') or '\\' in name or '..' in parts:
            raise ValueError('Unsafe distribution member')
        if any(part.lower() in ('tokens', 'token', 'archive', '.git', '.venv', '__pycache__') or part.startswith('.env') for part in parts):
            raise ValueError('Private or generated files in distribution')
        normalized = name if wheel else '/'.join(parts[1:])
        if normalized in files:
            raise ValueError('Duplicate distribution member')
        files[normalized] = contents
    return files


def package_payload(files):
    return {key: value for key, value in files.items() if key.startswith(PACKAGE + '/')}


def metadata(files, wheel):
    candidates = [key for key in files if key.endswith('.dist-info/METADATA')] if wheel else ['PKG-INFO']
    if len(candidates) != 1 or candidates[0] not in files:
        raise ValueError('Distribution metadata is missing or ambiguous')
    message = email.message_from_bytes(files[candidates[0]])
    if re.sub(r'[-_.]+', '-', message.get('Name', '')).lower() != 'wpp-whatsapp':
        raise ValueError('Unexpected package name')
    return message


def verify_dist(directory, source, expected=None):
    expected = expected or version(source)
    paths = sorted(path for path in Path(directory).glob('*') if path.name != '.gitignore')
    wheels = [path for path in paths if path.suffix == '.whl']
    sdists = [path for path in paths if path.name.endswith('.tar.gz')]
    if len(wheels) != 1 or len(sdists) != 1 or len(paths) != 2:
        raise ValueError('Build must contain exactly one wheel and one source distribution')
    source_payload = {f'{PACKAGE}/{path.relative_to(Path(source) / PACKAGE).as_posix()}': path.read_bytes()
                      for path in (Path(source) / PACKAGE).rglob('*') if path.is_file() and path.suffix in SUFFIXES}
    for asset in ASSETS:
        if f'{PACKAGE}/{asset}' not in source_payload:
            raise ValueError('Required JavaScript runtime is missing from source')
    for path, wheel in [(wheels[0], True), (sdists[0], False)]:
        files = archive_files(path, wheel)
        if metadata(files, wheel)['Version'] != expected:
            raise ValueError('Built version differs from selected release')
        if package_payload(files) != source_payload:
            raise ValueError('Built package payload differs from the selected source')
    print(f'Validated wheel, sdist and packaged runtime assets for {expected}')
    return paths


def compare_published(local_path, remote):
    wheel = local_path.suffix == '.whl'
    local = archive_files(local_path, wheel)
    published = archive_files(remote, wheel)
    if package_payload(local) != package_payload(published):
        raise ValueError('PyPI package payload differs from the release build')
    first, second = metadata(local, wheel), metadata(published, wheel)
    for field in ('Name', 'Version', 'Requires-Python', 'Requires-Dist', 'Provides-Extra'):
        if sorted(first.get_all(field, [])) != sorted(second.get_all(field, [])):
            raise ValueError('PyPI package metadata differs from the release build')


def verify_pypi(directory, source, attempts=12):
    expected = version(source)
    paths = verify_dist(directory, source, expected)
    for attempt in range(attempts):
        try:
            data = request_json(f'https://pypi.org/pypi/WPP-Whatsapp/{quote(expected, safe="")}/json')
            if data.get('info', {}).get('version') != expected:
                raise ValueError('Unexpected PyPI version')
            published = {entry['filename']: entry for entry in data.get('urls', []) if not entry.get('yanked')}
            if not all(path.name in published for path in paths):
                raise LookupError('PyPI files are not visible yet')
            for path in paths:
                entry = published[path.name]
                parsed = urlparse(entry['url'])
                if parsed.scheme != 'https' or parsed.hostname != 'files.pythonhosted.org':
                    raise ValueError('Unexpected PyPI asset host')
                with urlopen(entry['url'], timeout=30) as response:
                    raw = response.read()
                if hashlib.sha256(raw).hexdigest() != entry.get('digests', {}).get('sha256'):
                    raise ValueError('Published file digest mismatch')
                # Rebuild timestamps/build-tool versions may differ on recovery.
                # Compare all shipped package bytes and dependency metadata.
                compare_published(path, raw)
            print(f'Verified PyPI {expected}: wheel, sdist, metadata and runtime payloads')
            return
        except HTTPError as error:
            if error.code not in (404, 429, 500, 502, 503, 504):
                raise
        except (URLError, TimeoutError, LookupError):
            pass
        if attempt + 1 < attempts:
            time.sleep(5)
    raise RuntimeError('Published artifacts could not be verified on PyPI within the retry window')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['plan', 'dist', 'pypi'])
    parser.add_argument('--source', default='.')
    parser.add_argument('--dist', default='dist')
    args = parser.parse_args()
    if args.command == 'plan':
        plan(args.source)
    elif args.command == 'dist':
        verify_dist(args.dist, args.source)
    else:
        verify_pypi(args.dist, args.source)

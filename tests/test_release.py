"""Distribution and release checks, including manual recovery of old tags."""
import io
import json
import tarfile
import zipfile
from unittest.mock import patch

import pytest

from tools.verify_release import ASSETS, archive_files, compare_published, plan, verify_dist, version


def project(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'pyproject.toml').write_text('[project]\nname = "WPP_Whatsapp"\nversion = "1.2.0"\n', encoding='utf-8')
    package = source / 'WPP_Whatsapp'
    for asset in (*ASSETS, '__init__.py', 'core/commands.py'):
        file = package / asset
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text('COMMANDS = {}' if asset.endswith('.py') else '// fixture', encoding='utf-8')
    return source


def distributions(tmp_path, source, wheel_version='1.2.0', extra=None):
    directory = tmp_path / 'dist'
    directory.mkdir()
    files = {f'WPP_Whatsapp/{file.relative_to(source / "WPP_Whatsapp").as_posix()}': file.read_bytes()
             for file in (source / 'WPP_Whatsapp').rglob('*') if file.is_file()}
    if extra:
        files.update(extra)
    metadata = b'Name: WPP_Whatsapp\nVersion: 1.2.0\nRequires-Python: >=3.9\n'
    wheel = directory / 'wpp_whatsapp-1.2.0-py3-none-any.whl'
    with zipfile.ZipFile(wheel, 'w') as archive:
        for name, data in files.items():
            archive.writestr(name, data)
        archive.writestr('wpp_whatsapp-1.2.0.dist-info/METADATA', metadata.replace(b'1.2.0', wheel_version.encode()))
    with tarfile.open(directory / 'wpp_whatsapp-1.2.0.tar.gz', 'w:gz') as archive:
        for name, data in {**files, 'PKG-INFO': metadata}.items():
            member = tarfile.TarInfo('wpp_whatsapp-1.2.0/' + name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    return directory


def test_built_artifacts_match_version_and_every_package_byte(tmp_path):
    source = project(tmp_path)
    assert version(source) == '1.2.0'
    directory = distributions(tmp_path, source)
    assert len(verify_dist(directory, source)) == 2
    (source / 'WPP_Whatsapp/core/commands.py').write_text('COMMANDS = {"changed": "true"}', encoding='utf-8')
    with pytest.raises(ValueError, match='payload differs'):
        verify_dist(directory, source)


def test_mismatched_built_version_is_rejected(tmp_path):
    source = project(tmp_path)
    with pytest.raises(ValueError, match='version differs'):
        verify_dist(distributions(tmp_path, source, wheel_version='9.9.9'), source)


@pytest.mark.parametrize('member', ['tokens/session.json', 'archive/private.txt', '../private', '/private', 'WPP_Whatsapp/.env'])
def test_private_or_unsafe_archive_members_are_rejected(member):
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as archive:
        archive.writestr(member, 'private')
    with pytest.raises(ValueError):
        archive_files(data.getvalue(), True)


def test_pypi_recovery_compares_package_contents_instead_of_zip_timestamps(tmp_path):
    source = project(tmp_path)
    directory = distributions(tmp_path, source)
    wheel = next(directory.glob('*.whl'))
    compare_published(wheel, wheel.read_bytes())
    changed = io.BytesIO()
    with zipfile.ZipFile(wheel) as original, zipfile.ZipFile(changed, 'w') as archive:
        for name in original.namelist():
            archive.writestr(name, b'// wrong runtime' if name.endswith('wapi.js') else original.read(name))
    with pytest.raises(ValueError, match='PyPI package payload differs'):
        compare_published(wheel, changed.getvalue())


def event_environment(tmp_path, monkeypatch, tag='v1.2.0'):
    event = tmp_path / 'event.json'
    event.write_text(json.dumps({'inputs': {'release_tag': tag}}), encoding='utf-8')
    for key, value in {'GITHUB_EVENT_NAME': 'workflow_dispatch', 'GITHUB_EVENT_PATH': str(event),
                       'GITHUB_SHA': 'workflow-sha', 'GITHUB_REPOSITORY': 'owner/repo',
                       'GITHUB_OUTPUT': str(tmp_path / 'output')}.items():
        monkeypatch.setenv(key, value)


def test_manual_recovery_pins_tagged_commit_and_never_builds_default_branch(tmp_path, monkeypatch):
    source = project(tmp_path)
    event_environment(tmp_path, monkeypatch)
    with patch('tools.verify_release.request_json', return_value={'tag_name': 'v1.2.0', 'published_at': 'now'}), \
         patch('tools.verify_release.subprocess.check_output', side_effect=['tagged-sha\n', (source / 'pyproject.toml').read_text()]) as git:
        assert plan(source) == {'ref': 'tagged-sha', 'publish': 'true', 'tag': 'v1.2.0'}
    assert 'refs/tags/v1.2.0^{commit}' in git.call_args_list[0].args[0]
    assert 'tagged-sha:pyproject.toml' in git.call_args_list[1].args[0]


@pytest.mark.parametrize('tag', ['main', '../main', 'v1.2.0\npublish=true', '--help'])
def test_dispatch_rejects_non_version_tags(tmp_path, monkeypatch, tag):
    event_environment(tmp_path, monkeypatch, tag)
    with pytest.raises(ValueError, match='version tag'):
        plan(tmp_path)


def test_dispatch_rejects_drafts_and_version_mismatch(tmp_path, monkeypatch):
    event_environment(tmp_path, monkeypatch)
    with patch('tools.verify_release.request_json', return_value={'tag_name': 'v1.2.0', 'draft': True}):
        with pytest.raises(ValueError, match='published GitHub release'):
            plan(tmp_path)
    with patch('tools.verify_release.request_json', return_value={'tag_name': 'v1.2.0', 'published_at': 'now'}), \
         patch('tools.verify_release.subprocess.check_output', side_effect=['sha\n', '[project]\nversion = "1.1.0"\n']):
        with pytest.raises(ValueError, match='does not match'):
            plan(tmp_path)

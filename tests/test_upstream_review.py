"""Offline audit failure modes; never execute remote TypeScript."""

import io
import tarfile
from unittest.mock import Mock

import pytest

from tools.check_upstream import SourceReader, compare, exported_names, methods, read_archive


def test_public_exports_follow_reexports_and_do_not_expose_internal_helpers():
    files = {
        "src/chat/index.ts": "export * from './functions'; export {Foo as Bar} from './foo';",
        "src/chat/functions/index.ts": "export * from './send'; export * from '../index';",
        "src/chat/functions/send.ts": "export async function send() {} // export function fake() {}",
        "src/chat/functions/private.ts": "export function internal() {}",
    }
    assert exported_names(files, "src/chat/index.ts") == {"send", "Bar"}


def test_audit_surfaces_signature_changes_and_removals():
    old = methods(
        {
            "src/api/layers/test.layer.ts": "class Layer {\n  public async read(id: string) {}\n  private secret() {}\n}"
        }
    )
    new = methods(
        {
            "src/api/layers/test.layer.ts": "class Layer {\n  public async read(id: number) {}\n  public async added() {}\n}"
        }
    )
    diff = compare(old, new)["test.layer.ts"]
    assert diff == {"added": ["added"], "removed": [], "changed": ["read"]}
    assert compare({"chat": ["send"]}, {"chat": []})["chat"]["removed"] == ["send"]


def test_source_archive_is_read_without_extracting_links_or_files(tmp_path):
    content = io.BytesIO()
    with tarfile.open(fileobj=content, mode="w:gz") as archive:
        file = tarfile.TarInfo("repo/src/chat/index.ts")
        value = b"export function send() {}"
        file.size = len(value)
        archive.addfile(file, io.BytesIO(value))
        link = tarfile.TarInfo("repo/src/chat/link.ts")
        link.type, link.linkname = tarfile.SYMTYPE, "/etc/passwd"
        archive.addfile(link)
    assert read_archive(content.getvalue()) == {"src/chat/index.ts": value.decode()}
    assert not list(tmp_path.iterdir())


def test_network_download_is_bounded_and_does_not_send_token_to_codeload(monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "secret")
    reader = SourceReader()
    reply = Mock()
    reply.__enter__ = Mock(return_value=reply)
    reply.__exit__ = Mock(return_value=False)
    reply.iter_content.return_value = [b"a" * 10]
    reader.session.get = Mock(return_value=reply)
    with monkeypatch.context() as isolated:
        isolated.setattr("tools.check_upstream.MAX_DOWNLOAD", 5)
        with pytest.raises(ValueError, match="limit"):
            reader.fetch("https://codeload.github.com/source")
    assert reader.session.get.call_args.kwargs["headers"] == {}
    reader.session.close()

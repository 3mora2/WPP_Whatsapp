"""Read-only upstream audit. Parse pinned TypeScript sources without executing them.

This is an API-surface/signature review aid, not proof of WhatsApp compatibility.
No bundle or trusted baseline is automatically replaced.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import tarfile
import time
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
MAX_DOWNLOAD = 32 * 1024 * 1024
MAX_SOURCE = 64 * 1024 * 1024
MAX_ARCHIVE = 256 * 1024 * 1024


class SourceReader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "WPP-Whatsapp-upstream-audit"
        self.deadline = time.monotonic() + 180

    def fetch(self, url: str, *, github_api=False) -> bytes:
        headers = {}
        if github_api and os.environ.get("GH_TOKEN"):
            headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
        output = bytearray()
        with self.session.get(url, headers=headers, timeout=(10, 30), stream=True) as reply:
            reply.raise_for_status()
            for chunk in reply.iter_content(65536):
                if time.monotonic() > self.deadline:
                    raise TimeoutError("Upstream audit exceeded its deadline")
                output.extend(chunk)
                if len(output) > MAX_DOWNLOAD:
                    raise ValueError("Upstream response exceeds the configured limit")
        return bytes(output)

    def commit(self, repo: str) -> str:
        metadata = json.loads(
            self.fetch(f"https://api.github.com/repos/wppconnect-team/{repo}", github_api=True)
        )
        branch = quote(metadata["default_branch"], safe="")
        value = json.loads(
            self.fetch(
                f"https://api.github.com/repos/wppconnect-team/{repo}/commits/{branch}",
                github_api=True,
            )
        )
        sha = value["sha"]
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError("Invalid upstream commit")
        return sha

    def source(self, repo: str, sha: str) -> tuple[dict[str, str], str]:
        if repo not in {"wa-js", "wppconnect"} or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError("Invalid source selection")
        content = self.fetch(f"https://codeload.github.com/wppconnect-team/{repo}/tar.gz/{sha}")
        return read_archive(content), hashlib.sha256(content).hexdigest()


def read_archive(content: bytes) -> dict[str, str]:
    result, size, archive_size, entries = {}, 0, 0, 0
    with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as archive:
        for member in archive:
            archive_size += member.size
            entries += 1
            if archive_size > MAX_ARCHIVE or entries > 50000:
                raise ValueError("Upstream archive exceeds the configured limit")
            # Never extract paths, symlinks or executable code to disk.
            relative = member.name.split("/", 1)[-1]
            if (
                not member.isfile()
                or not relative.startswith("src/")
                or not relative.endswith(".ts")
            ):
                continue
            size += member.size
            if member.size > 2 * 1024 * 1024 or size > MAX_SOURCE:
                raise ValueError("Upstream sources exceed the configured limit")
            handle = archive.extractfile(member)
            if handle is not None:
                result[relative] = handle.read().decode("utf-8")
    if not result:
        raise ValueError("No TypeScript source found")
    return result


def exported_names(files: dict[str, str], path: str, seen=None) -> set[str]:
    seen = set() if seen is None else seen
    if path in seen:
        return set()
    seen.add(path)
    source = re.sub(r"/\*.*?\*/|//[^\n]*", "", files.get(path, ""), flags=re.S)
    names = set(
        re.findall(
            r"\bexport\s+(?:declare\s+)?(?:async\s+)?(?:function|interface|type|class|enum|const|let)\s+(\w+)",
            source,
        )
    )
    for block in re.findall(r"\bexport\s*\{([^}]+)\}", source):
        for item in block.split(","):
            name = re.sub(r"^type\s+", "", item.strip()).split(" as ")[-1].strip()
            if re.fullmatch(r"\w+", name):
                names.add(name)
    for relative in re.findall(r"\bexport\s*\*\s*from\s*['\"]([^'\"]+)['\"]", source):
        if not relative.startswith("."):
            continue
        from posixpath import dirname, normpath

        target = normpath(dirname(path) + "/" + relative)
        target = target + ".ts" if target + ".ts" in files else target + "/index.ts"
        names.update(exported_names(files, target, seen))
    return names


def methods(files: dict[str, str]) -> dict[str, dict[str, str]]:
    result = {}
    for path, source in files.items():
        if not re.fullmatch(r"src/api/layers/[^/]+\.layer\.ts", path):
            continue
        found = {}
        for match in re.finditer(
            r"^  (?:(?:public|async|override|static)\s+)*(\w+)\s*\(", source, flags=re.M
        ):
            name = match[1]
            if name in {"constructor", "if", "for", "while", "switch", "catch"}:
                continue
            # Balanced parameter delimiters include nested defaults and function types.
            depth, end = 1, match.end()
            while end < len(source) and depth:
                depth += (source[end] == "(") - (source[end] == ")")
                end += 1
            if depth:
                raise ValueError("Unbalanced upstream method signature")
            found[name] = " ".join(source[match.start() : end].split())
        result[Path(path).name] = found
    return result


def compare(old: dict, new: dict) -> dict:
    return {
        key: {
            "added": sorted(set(new.get(key, {})) - set(old.get(key, {}))),
            "removed": sorted(set(old.get(key, {})) - set(new.get(key, {}))),
            "changed": sorted(
                name
                for name in set(old.get(key, {})) & set(new.get(key, {}))
                if isinstance(old[key], dict) and old[key][name] != new[key][name]
            ),
        }
        for key in sorted(set(old) | set(new))
    }


def audit(reader: SourceReader, baseline: dict) -> dict:
    report = {
        "schema_version": 1,
        "scope": "static API surface; authenticated runtime tests required",
        "sources": {},
        "exports": {},
        "methods": {},
    }
    for key, repo in (("wppconnect", "wppconnect"), ("wa-js", "wa-js")):
        old_sha, new_sha = baseline[key]["sha"], reader.commit(repo)
        previous, previous_digest = reader.source(repo, old_sha)
        current, digest = (
            reader.source(repo, new_sha) if new_sha != old_sha else (previous, previous_digest)
        )
        report["sources"][key] = {
            "baseline": old_sha,
            "candidate": new_sha,
            "archive_sha256": digest,
        }
        if key == "wa-js":
            old = {
                ns: sorted(exported_names(previous, f"src/{ns}/index.ts"))
                for ns in baseline["exports"]
            }
            new = {
                ns: sorted(exported_names(current, f"src/{ns}/index.ts"))
                for ns in baseline["exports"]
            }
            report["exports"] = compare(old, new)
            # The old fixture includes internal exported TS helpers that are not
            # re-exported by the public namespace. Validate the actual Python calls.
            used = set()
            for path in (ROOT / "WPP_Whatsapp").rglob("*.py"):
                if path.name != "wapi.py":
                    used.update(
                        re.findall(r"WPP\.(\w+)\.(\w+)\s*\(", path.read_text(encoding="utf-8"))
                    )
            if any(
                name not in old.get(ns, []) for ns, name in used if ns not in {"whatsapp", "loader"}
            ):
                raise ValueError(
                    "Baseline export parser does not cover a referenced runtime function"
                )
        else:
            old, new = methods(previous), methods(current)
            if any(
                set(values) - set(old.get(layer, {}))
                for layer, values in baseline["public_methods"].items()
            ):
                raise ValueError("Baseline method parser does not cover the recorded contract")
            report["methods"] = compare(old, new)
    report["review_required"] = any(
        any(diff[category] for category in ("added", "removed", "changed"))
        for section in ("exports", "methods")
        for diff in report[section].values()
    )
    report["potential_breaking_change"] = any(
        diff["removed"] or diff["changed"]
        for section in ("exports", "methods")
        for diff in report[section].values()
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "archive/upstream-report.json")
    args = parser.parse_args()
    baseline = json.loads((ROOT / "tests/fixtures/upstream_contract.json").read_text())
    reader = SourceReader()
    try:
        report = audit(reader, baseline)
    finally:
        reader.session.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps({key: report[key] for key in ("review_required", "potential_breaking_change")})
    )
    return 2 if report["potential_breaking_change"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

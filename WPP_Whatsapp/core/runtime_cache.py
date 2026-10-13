"""Atomic, content-verified cache for runtime assets; metadata discovery stays live."""

import hashlib
import json
import os
import tempfile
from pathlib import Path


class RuntimeCache:
    def __init__(self, directory):
        self.directory = Path(directory)

    def _paths(self, url):
        key = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.directory / (key + ".js"), self.directory / (key + ".json")

    def read(self, url):
        source, manifest = self._paths(url)
        try:
            raw = source.read_bytes()
            metadata = json.loads(manifest.read_text(encoding="utf-8"))
            if (
                metadata.get("url") != url
                or metadata.get("sha256") != hashlib.sha256(raw).hexdigest()
            ):
                return None
            return raw.decode("utf-8")
        except (OSError, ValueError, UnicodeError):
            return None

    def write(self, url, content):
        self.directory.mkdir(parents=True, exist_ok=True)
        raw = content.encode("utf-8")
        source, manifest = self._paths(url)
        metadata = json.dumps({"url": url, "sha256": hashlib.sha256(raw).hexdigest()}).encode(
            "utf-8"
        )
        for target, value in ((source, raw), (manifest, metadata)):
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=self.directory, delete=False) as stream:
                    temporary = stream.name
                    stream.write(value)
                os.replace(temporary, target)
            finally:
                if temporary and os.path.exists(temporary):
                    os.unlink(temporary)

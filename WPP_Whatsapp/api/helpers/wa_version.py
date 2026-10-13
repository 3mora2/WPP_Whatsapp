import asyncio
import os
import re
from pathlib import Path

from nodesemver import max_satisfying, _sorted, satisfies
import aiohttp

from WPP_Whatsapp.api.const import Logger


async def getAvailableVersions(session, versionMatch=None, includePrerelease=True):
    async with session.get("https://api.github.com/repos/wppconnect-team/wa-version/contents/html") as response:
        # Return the JSON content of the response using 'response.json()'
        if not response.ok:
            return []

        entries = await response.json()
        if not isinstance(entries, list):
            raise ValueError("Invalid WhatsApp version list")
        versions = []
        for entry in entries:
            name = entry.get('name', '') if isinstance(entry, dict) else ''
            if not name.endswith('.html'):
                continue
            value = name[:-5]
            try:
                if satisfies(value, '*', include_prerelease=True):
                    versions.append(value)
            except ValueError:
                continue
        sorted_versions = _sorted(versions)

        if versionMatch:
            return [v for v in sorted_versions if satisfies(v, versionMatch, include_prerelease=includePrerelease)]
        else:
            return sorted_versions


async def getLatestVersion(session, versionMatch='*', includePrerelease=True):
    versions = await getAvailableVersions(session=session)

    max_version = max_satisfying(versions, versionMatch, include_prerelease=includePrerelease)
    if not max_version:
        raise ValueError(f"Version not available for {versionMatch}")
    return max_version.raw


async def getPageContent(versionMatch=None, includePrerelease=True):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30, connect=5)) as session:
        versions = await getAvailableVersions(session=session)

        max_version = max_satisfying(versions, versionMatch or '*', include_prerelease=includePrerelease)

        if not max_version:
            raise ValueError(f"Version not available for {versionMatch}")

        async with session.get(
                f"https://raw.githubusercontent.com/wppconnect-team/wa-version/main/html/{max_version.raw}.html") as response:
            # Return the JSON content of the response using 'response.json()'
            response.raise_for_status()
            return await response.text()

URL_RE = re.compile(r"^https?://", re.IGNORECASE)
WA_JS_RELEASES_URL = "https://api.github.com/repos/wppconnect-team/wa-js/releases"
WA_JS_NIGHTLY_URL = "https://github.com/wppconnect-team/wa-js/releases/download/nightly/wppconnect-wa.js"
WA_JS_FETCH_TIMEOUT = 30


def _bundled_wajs():
    path = Path(__file__).resolve().parents[2] / "js_lib" / "wppconnect-wa.js"
    return {"content": path.read_text(encoding="utf-8")}


def _release_asset(release):
    if not isinstance(release, dict):
        raise ValueError("Invalid WA-JS release metadata")
    assets = release.get("assets") or []
    if not isinstance(assets, list):
        raise ValueError("Invalid WA-JS release assets")
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        url = asset.get("browser_download_url")
        if asset.get("name") == "wppconnect-wa.js" and isinstance(url, str) and URL_RE.match(url):
            return url
    return None


async def _download_wajs(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        content = await response.text(encoding="utf-8")
        if (not content.strip() or response.content_type in ("text/html", "application/json")
                or content.lstrip().lower().startswith(("<!doctype html", "<html"))):
            raise ValueError("WA-JS download did not contain JavaScript")
        return {"content": content}


async def _versioned_wajs_url(session, version):
    # GitHub defaults to 30 releases per page. Older explicit versions must
    # also be searchable, without silently substituting an unrelated version.
    for page in range(1, 11):
        async with session.get(WA_JS_RELEASES_URL, params={"per_page": 100, "page": page}) as response:
            response.raise_for_status()
            releases = await response.json()
        if not isinstance(releases, list):
            raise ValueError("Invalid WA-JS release list")
        tags = {}
        for release in releases:
            if not isinstance(release, dict) or release.get("draft"):
                continue
            tag = release.get("tag_name")
            url = _release_asset(release)
            if not isinstance(tag, str) or not url:
                continue
            try:
                if satisfies(tag, "*", include_prerelease=True):
                    tags[tag] = url
            except ValueError:
                continue  # e.g. the nightly release tag
        selected = max_satisfying(tags, version, include_prerelease=True)
        if selected:
            return tags[selected]
        if len(releases) < 100:
            break
    raise ValueError(f"No WA-JS release with a JavaScript asset matches {version!r}")


async def _remote_wajs(version):
    timeout = aiohttp.ClientTimeout(total=20, connect=5)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        if version in (None, "latest"):
            async with session.get(WA_JS_RELEASES_URL + "/latest") as response:
                response.raise_for_status()
                release = await response.json()
            if not isinstance(release, dict) or release.get("draft") or release.get("prerelease"):
                raise ValueError("No stable WA-JS release available")
            url = _release_asset(release)
            if not url:
                raise ValueError("Latest WA-JS release has no JavaScript asset")
        elif version == "nightly":
            url = WA_JS_NIGHTLY_URL
        elif URL_RE.match(version):
            url = version
        else:
            url = await _versioned_wajs_url(session, version)
        return await _download_wajs(session, url)


async def getWaJs(version=None):
    """Try the latest stable release first; use bundled WA-JS if unavailable.

    Explicit versions, nightly builds, URLs and local files are honored and
    report failures rather than silently loading a different runtime.
    Use ``version="bundled"`` to skip network access entirely.
    """
    if version is not None:
        version = os.fspath(version) if isinstance(version, os.PathLike) else str(version)
        if version == "bundled":
            return _bundled_wajs()
        if not URL_RE.match(version) and os.path.isfile(version):
            return {"content": Path(version).read_text(encoding="utf-8")}
    try:
        return await asyncio.wait_for(_remote_wajs(version), timeout=WA_JS_FETCH_TIMEOUT)
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, UnicodeError) as error:
        if version not in (None, "latest"):
            raise
        Logger.warning("Could not load latest WA-JS (%s); using bundled runtime", type(error).__name__)
        return _bundled_wajs()

import os
from nodesemver import max_satisfying, _sorted, satisfies
import requests


def getAvailableVersions(versionMatch=None, includePrerelease=True):
    r = requests.get("https://api.github.com/repos/wppconnect-team/wa-version/contents/html")
    if not r.ok:
        return []
    versions = [os.path.splitext(da.get("name"))[0] for da in r.json()]
    sorted_versions = _sorted(versions)

    if versionMatch:
        return [v for v in sorted_versions if satisfies(v, versionMatch, include_prerelease=includePrerelease)]
    else:
        return sorted_versions


def getLatestVersion(versionMatch='*', includePrerelease=True):
    versions = getAvailableVersions()

    max_version = max_satisfying(versions, versionMatch, include_prerelease=includePrerelease)

    return (max_version or versions[-1]).raw


def getPageContent(versionMatch=None, includePrerelease=True):
    if versionMatch is None:
        versionMatch = getLatestVersion()

    versions = getAvailableVersions()

    max_version = max_satisfying(versions, versionMatch, include_prerelease=includePrerelease)

    if not max_version:
        raise ValueError(f"Version not available for {versionMatch}")
    r = requests.get(f"https://raw.githubusercontent.com/wppconnect-team/wa-version/main/html/{max_version.raw}.html")
    if r.ok:
        return r.text

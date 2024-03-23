import os
from nodesemver import max_satisfying, _sorted, satisfies
import requests
import aiohttp


async def getAvailableVersions(session, versionMatch=None, includePrerelease=True):
    async with session.get("https://api.github.com/repos/wppconnect-team/wa-version/contents/html") as response:
        # Return the JSON content of the response using 'response.json()'
        if not response.ok:
            return []

        versions = [os.path.splitext(da.get("name"))[0] for da in await response.json()]
        sorted_versions = _sorted(versions)

        if versionMatch:
            return [v for v in sorted_versions if satisfies(v, versionMatch, include_prerelease=includePrerelease)]
        else:
            return sorted_versions


async def getLatestVersion(session, versionMatch='*', includePrerelease=True):
    versions = await getAvailableVersions(session=session)

    max_version = max_satisfying(versions, versionMatch, include_prerelease=includePrerelease)

    return (max_version or versions[-1]).raw


async def getPageContent(versionMatch=None, includePrerelease=True):
    async with aiohttp.ClientSession() as session:
        if versionMatch is None:
            versionMatch = await getLatestVersion(session=session)

        versions = await getAvailableVersions(session=session)

        max_version = max_satisfying(versions, versionMatch, include_prerelease=includePrerelease)

        if not max_version:
            raise ValueError(f"Version not available for {versionMatch}")

        async with session.get(f"https://raw.githubusercontent.com/wppconnect-team/wa-version/main/html/{max_version.raw}.html") as response:
            # Return the JSON content of the response using 'response.json()'
            if response.ok:
                return await response.text()



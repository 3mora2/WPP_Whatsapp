import base64

import aiohttp
import re
from typing import List, Union


async def downloadFileToBase64(_path: str, _mines: List[Union[str, re.Pattern]] = []) -> Union[str, bool]:
    if not isinstance(_mines, list):
        print(f'set mines string array, not "{type(_mines).__name__}"')
        return False

    re_http = re.compile(r'^https?:')

    if not re_http.match(_path):
        return False

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(_path) as response:
                response.raise_for_status()
                content = await response.read()

        mimeType = response.headers['content-type']

        if _mines:
            isValidMime = any((m.fullmatch(mimeType) if isinstance(m, re.Pattern) else m == mimeType) for m in _mines)
            if not isValidMime:
                print(f'Content-Type "{mimeType}" of {_path} is not allowed')
                return False
        archive = base64.b64encode(content)
        base64_content = archive.decode("utf-8")

        return f'data:{mimeType};base64,{base64_content}'
    except Exception as e:
        print(e)

    return False

if __name__ == '__main__':
    import asyncio
    print(asyncio.run(downloadFileToBase64("https://m.media-amazon.com/images/I/41F9VpcaslL.jpg")))
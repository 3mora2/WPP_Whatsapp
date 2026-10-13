"""Download caller-selected media to a new output file; existing files are preserved."""

import argparse
import base64
from pathlib import Path

from WPP_Whatsapp import Create


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("message_id")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output file; the path already exists")
    if not args.output.parent.is_dir():
        parser.error("The output directory must already exist")
    with Create("download-example", autoClose=0) as client:
        media = client.downloadMedia(args.message_id)
        if not isinstance(media, str) or not media:
            raise ValueError("No media returned for that message")
        payload = media
        if media.startswith("data:"):
            header, separator, payload = media.partition(",")
            if not separator or ";base64" not in header:
                raise ValueError("Expected base64 media data")
        contents = base64.b64decode(payload, validate=True)
        with args.output.open("xb") as stream:
            stream.write(contents)
        print("Saved bytes:", len(contents))


if __name__ == "__main__":
    main()

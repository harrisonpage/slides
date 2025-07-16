#!/usr/bin/env python3

import argparse
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
import pprint
import re
import sys
from typing import Dict, List
import requests
from PIL import Image

URL_PATTERN = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
HASHTAG_PATTERN = re.compile(r'#\w+')

def resize_and_compress_image(path: str, max_bytes: int = 1_000_000) -> bytes:
    # Load image
    with Image.open(path) as img:
        img = img.convert("RGB")  # Ensure JPEG-compatible mode

        # Start with a rough target size
        quality = 85
        width, height = img.size

        while True:
            # Resize proportionally (e.g., 75% each time)
            buffer = BytesIO()
            resized = img.resize((int(width), int(height)), Image.Resampling.LANCZOS)
            resized.save(buffer, format="JPEG", quality=quality, optimize=True)
            data = buffer.getvalue()

            if len(data) <= max_bytes or (width < 256 or height < 256):
                return data

            # If too big, reduce quality or scale
            quality -= 5
            width = int(width * 0.9)
            height = int(height * 0.9)

            if quality < 30:
                raise Exception(f"Could not compress image below {max_bytes} bytes")

def generate_facets_from_links_and_hashtags_in_text(text):
    '''Generate atproto facets for each URL and hashtag in the text with correct byte offsets'''
    facets = []

    byte_offsets = []
    current_byte_offset = 0
    for char in text:
        char_encoded = char.encode('utf-8')
        byte_offsets.append(current_byte_offset)
        current_byte_offset += len(char_encoded)
    byte_offsets.append(current_byte_offset)

    for match in re.finditer(f'{URL_PATTERN.pattern}|{HASHTAG_PATTERN.pattern}', text):
        matched_text = match.group(0)
        char_start, char_end = match.start(), match.end()

        byte_start = byte_offsets[char_start]
        byte_end = byte_offsets[char_end]

        if matched_text.startswith('#'):
            facets.append(gen_hashtag(byte_start, byte_end, matched_text[1:]))
        else:
            facets.append(gen_link(byte_start, byte_end, matched_text))

    return facets

def gen_link(start, end, uri):
    '''Generate a link facet for URLs'''
    return {
        "index": {
            "byteStart": start,
            "byteEnd": end
        },
        "features": [{
            "$type": "app.bsky.richtext.facet#link",
            "uri": uri
        }]
    }

def gen_hashtag(start, end, tag):
    '''Generate a facet for hashtags'''
    return {
        "index": {
            "byteStart": start,
            "byteEnd": end
        },
        "features": [{
            "$type": "app.bsky.richtext.facet#tag",
            "tag": tag
        }]
    }

def bsky_login_session(pds_url: str, handle: str, password: str) -> Dict:
    resp = requests.post(
        pds_url + "/xrpc/com.atproto.server.createSession",
        json={"identifier": handle, "password": password},
    )
    resp.raise_for_status()
    return resp.json()

def upload_file(pds_url, access_token, filename, img_bytes) -> Dict:
    suffix = filename.split(".")[-1].lower()
    mimetype = "application/octet-stream"
    if suffix in ["png"]:
        mimetype = "image/png"
    elif suffix in ["jpeg", "jpg"]:
        mimetype = "image/jpeg"
    elif suffix in ["webp"]:
        mimetype = "image/webp"
    elif suffix in ['gif']:
        mimetype = 'image/gif'

    resp = requests.post(
        pds_url + "/xrpc/com.atproto.repo.uploadBlob",
        headers={
            "Content-Type": mimetype,
            "Authorization": "Bearer " + access_token,
        },
        data=img_bytes,
    )
    resp.raise_for_status()
    return resp.json()["blob"]

def upload_images(pds_url: str, access_token: str, image_paths: List[str], alt_text: str) -> Dict:
    images = []
    for ip in image_paths:
        img_bytes = resize_and_compress_image(ip, max_bytes=1_000_000)
        blob = upload_file(pds_url, access_token, ip, img_bytes)
        images.append({"alt": alt_text or "", "image": blob})
    return {
        "$type": "app.bsky.embed.images",
        "images": images,
    }

def hash_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "images",
        metavar="IMAGE",
        nargs="+",
        help="Path(s) to image file(s) to upload",
    )
    parser.add_argument('--username', default=os.environ.get('BLUESKY_HANDLE'))
    parser.add_argument('--password', default=os.environ.get('BLUESKY_PASSWORD'))

    args = parser.parse_args()
    username = args.username
    password = args.password
    filepaths = args.images
    firstfile = filepaths[0]
    hash_id = hash_file(firstfile)

    json_path = f"data/{hash_id}.json"
    print(f"💾 Loading {json_path}")

    with open(json_path, "r") as f:
        data = json.load(f)

    pprint.pprint(data)

    identifier_path = f"data/{hash_id}.id"
    with open(identifier_path, "r") as f:
        identifier = f.readline().strip()
    print(f"🍔 {identifier}")

    print(f"🐦 Logging into Bluesky as {username}")

    bluesky = bsky_login_session(
        'https://bsky.social',
        username,
        password,
    )

    # trailing "Z" is preferred over "+00:00"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    print(f"📅 {now}")

    url = f"""https://archive.org/details/{identifier}"""
    buf = url + " https://harrison.photography/way-we-was/"
    if 'date' in data and data['date'] != "":
        buf = data['date'] + "\n\n" + url
    buf += "\n\n"

    if 'tags' in data and len(data['tags']):
        for tag in data['tags']:
            tag = tag.strip()
            tag = tag.replace(' ', '')
            tag = tag.lower()
            if len(tag) == 0:
                continue
            t = f'#{tag} '
            buf += t

    buf += "#35mm #scan #vernacular #found #anonymous #photography #history"

    facets = generate_facets_from_links_and_hashtags_in_text(buf)
    post = {
        "$type": "app.bsky.feed.post",
        "text": buf,
        "createdAt": now,
        "facets": facets,
    }
    post["embed"] = upload_images(
        'https://bsky.social',
        bluesky["accessJwt"],
        [ firstfile ],
        data['description'],
    )
    print(json.dumps(post, indent=4))

    resp = requests.post(
        'https://bsky.social' + "/xrpc/com.atproto.repo.createRecord",
        headers={"Authorization": "Bearer " + bluesky["accessJwt"]},
        json={
            "repo": bluesky["did"],
            "collection": "app.bsky.feed.post",
            "record": post,
        },
    )
    resp.raise_for_status()
    print(json.dumps(resp.json(), indent=4))

    if resp.ok:
        with open(f"data/{hash_id}.bluesky", "w") as f:
            f.write(now)

    return 0

if __name__ == "__main__":
    sys.exit(main())

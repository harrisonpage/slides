#!/usr/bin/env python3

import argparse
import datetime
import hashlib
import json
import os
import pprint
import re
import sys
from typing import cast
from internetarchive import get_item
import requests

def normalize_identifier(title: str, hash_suffix: str) -> str:
    # Convert to lowercase
    identifier = title.lower()

    # Replace spaces and commas with dashes
    identifier = identifier.replace(" ", "-").replace(",", "-")

    # Remove characters that are not a-z, 0-9, -, _, or .
    identifier = re.sub(r"[^a-z0-9_.-]", "", identifier)

    # Remove duplicate dashes or periods
    identifier = re.sub(r"[-.]{2,}", "-", identifier)

    # Ensure it starts with a letter or digit
    if not re.match(r"^[a-z0-9]", identifier):
        identifier = "x" + identifier

    # Truncate to fit within max length when adding suffix
    max_prefix_len = 100 - len(hash_suffix) - 1  # for the dash
    identifier = identifier[:max_prefix_len]

    # Append unique suffix
    return f"{identifier}-{hash_suffix}"

def hash_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

parser = argparse.ArgumentParser(
    description="Upload one or more images to the Internet Archive."
)
parser.add_argument(
    "images",
    metavar="IMAGE",
    nargs="+",
    help="Path(s) to image file(s) to upload",
)
parser.add_argument(
    "--suffix",
    help="Optional suffix to append to the generated identifier",
)
parser.add_argument(
    "--date",
    help="Optional value for date metadata, overwrites applied date",
)

args = parser.parse_args()
filepaths = args.images
suffix = args.suffix
when = args.date

pprint.pprint(filepaths)

firstfile = filepaths[0]
filename = os.path.basename(firstfile)
timestamp = os.path.getmtime(firstfile)
scandate = datetime.datetime.fromtimestamp(timestamp).strftime("%Y%m%d%H%M%S")
hash_id = hash_file(firstfile)

json_path = f"data/{hash_id}.json"
print(f"💾 Loading {json_path}")

with open(json_path, "r") as f:
    data = json.load(f)

identifier = data.get("title", "")
if identifier == "":
    identifier = normalize_identifier(filename, hash_id)
else:
    identifier = normalize_identifier(identifier, hash_id)

if suffix:
    identifier += "-" + suffix

print("📂 Archiving:", identifier)

# https://archive.org/developers/metadata-schema/index.html
metadata = {
    'mediatype': 'image',
    'collection': 'opensource_media',
    'creator': 'Anonymous',
    'contributor': "Harrison Page <harrison@fogbelt.org>",
    'description': data.get("description"),
    'licenseurl': "https://creativecommons.org/publicdomain/zero/1.0/",
    'scanner': "OpticFilm 8300i; QuickScan Plus OF8300i; ",
    'scandate': scandate,
    'notes': "Vernacular 35mm slide (photographer unknown)",
    'source': "Personal archive of harrison.page",
}

if data.get("title", "").strip() != "":
    metadata['title'] = data.get("title")

if data.get("color", "").strip() != "":
    metadata['color'] = data.get("color")

if len(data.get("tags", [])):
    metadata['subject'] = data.get("tags")

if when:
    metadata['date'] = when

pprint.pprint(metadata)

item = get_item(identifier)
print("🌐 Identifier:", item.identifier)

with open(f"data/{hash_id}.id", "w") as f:
    f.write(identifier)

upload_files = {}  # key: remote filename, value: file-like object
open_files = []    # keep track of open file handles to close later

for i, path in enumerate(filepaths):
    base = os.path.basename(path)
    if i == 0:
        # First image gets special name for thumbnail
        name, ext = os.path.splitext(base)
        remote_name = f"001-{name}{ext}"
    else:
        remote_name = base

    f = open(path, "rb")
    f.seek(0) # 🔥
    open_files.append(f)
    upload_files[remote_name] = f

results = item.upload(upload_files, metadata=metadata, verbose=True)

# Close all file handles after upload
for f in open_files:
    f.close()

ok = False
for result in results:
    response = cast(requests.Response, result)

    if response.status_code == 200:
        ok = True
    else:
        print(f"❌ Upload failed: {response.status_code} — {response.reason}")
        print(response.text)
        sys.exit(1)

print(f"✅ Upload(s) succeeded https://archive.org/details/{item.identifier}")

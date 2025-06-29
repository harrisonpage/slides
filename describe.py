#!/usr/bin/env python3

import base64
import json
import re
import sys
import os
import time
import hashlib
import pprint
from typing import cast
import openai
from openai.types.chat import ChatCompletionMessageParam

openai.api_key = os.getenv("OPENAI_API_KEY")

BASE_PROMPT = """You will be shown multiple scanned 35mm slide images. Please analyze them together for archival metadata and alt-text purposes.

Write a single combined description of the group. Describe only what is clearly visible in the images. Do not speculate or guess a decade unless there is direct visual evidence (e.g., a car model or a dated sign). Avoid vague phrases like 'mid-20th-century.'

Then, suggest a single short title for the group (5 to 12 words).

Determine whether the set of images is in color or black and white overall. If unsure, choose 'B&W'. Use only the values: 'color' or 'B&W'.

Generate 3-5 tags that are specific to the photograph. Examples of useful tags would be "police", "beach", "fog". Do not generate tags for vague terms like "person" or "mid-century", "urban" or "car".

Finally, if a year is present, use that value for the date field below. Do not guess. Full day/month/year is great, year is fine, even "circa 1970" is fine if you are reasonably certain.

Respond in this exact JSON format:
{
    "title": "...",
    "description": "...",
    "color": "color" or "B&W",
    "date": "...",
    "tags": "tags go here"
}
Return only valid JSON. Do not include any explanation, comments, or markdown formatting. Do not wrap the output in triple backticks. Just return the raw JSON string.
"""

def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def hash_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} image1.jpg [image2.jpg ...]")
    sys.exit(1)

image_paths = [p for p in sys.argv[1:] if os.path.isfile(p)]
if not image_paths:
    print("❌ No valid images provided.", file=sys.stderr)
    sys.exit(1)

# Build image payloads
image_payloads = [
    {
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{encode_image(path)}"},
    }
    for path in image_paths
]

CUSTOM_PROMPT = """

Use the file paths to round out the image description if they are helpful. The file names are:
"""

for path in image_paths:
    CUSTOM_PROMPT += f"""
* {path}
"""

# Use md5 of the first image as output filename
hash_id = hash_file(image_paths[0])
print(f"🔒 Hash: {hash_id}")

json_path = f"data/{hash_id}.json"
print(f"💾 File: {json_path}")

os.makedirs("data", exist_ok=True)

try:
    print("💾 Connecting to OpenAI...")
    client = openai.OpenAI()
    messages = cast(list[ChatCompletionMessageParam], [
        {
            "role": "user",
            "content": [{"type": "text", "text": BASE_PROMPT + CUSTOM_PROMPT}] + image_payloads,
        }
    ])

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )

    content = response.choices[0].message.content

    if not content:
        print("❌ No content returned.", file=sys.stderr)
        sys.exit(1)

    # Remove possible markdown formatting
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.IGNORECASE)

    try:
        data = json.loads(content)
        pprint.pprint(data)
        title = data.get("title", "").strip()
        description = data.get("description", "").strip()
        color = data.get("color", "").strip()

        if not title or not description or color not in ("color", "B&W"):
            print("❌ Incomplete or invalid metadata received.", file=sys.stderr)
            sys.exit(1)

        metadata = {
            "title": title,
            "description": description,
            "color": color,
            "images": image_paths,
            "hash": hash_id,
            "ts": time.time(),
        }

        if (data.get("date", "") != ""):
            metadata['date'] = data.get('date')

        tags = data.get('tags', "")
        if isinstance(tags, str):
            print("😰 Tags returned as strings for some goddamn reason")
            tags = tags.split(", ")

        if len(tags):
            metadata['tags'] = tags

        with open(json_path, "w") as f:
            json.dump(metadata, f, indent=2)
            f.write("\n")

        print(f"✅ Wrote metadata to {json_path}")
        pprint.pprint(metadata)

    except json.JSONDecodeError:
        print("❌ Failed to parse JSON:", file=sys.stderr)
        print("Raw response:\n", content)
        sys.exit(1)

except Exception as e:
    print(f"❌ API request failed: {e}", file=sys.stderr)
    sys.exit(1)

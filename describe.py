#!/usr/bin/env python3

import base64
import sys
import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} path/to/image.jpg")
    sys.exit(1)

filepath = sys.argv[1]
filename = os.path.basename(filepath)
DESC = f"data/{filename}.desc"

with open(filepath, "rb") as f:
    base64_image = base64.b64encode(f.read()).decode("utf-8")

try:
    client = openai.OpenAI()

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
    )

    content = response.choices[0].message.content
    if not content:
        print("No content returned.", file=sys.stderr)
    else:
        description = content.strip()
        if description:
            with open(DESC, "w") as out:
                out.write(description + "\n")
            print(f"{filepath}: {description}")
        else:
            print("No description returned.", file=sys.stderr)
except Exception as e:
    print(f"API request failed: {e}", file=sys.stderr)
    sys.exit(1)

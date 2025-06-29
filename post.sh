#!/usr/bin/env bash

set -e
cd "$(dirname "$0")"

die () {
    echo >&2 "$@"
    exit 1
}

[ "$#" -lt 1 ] && die "Usage: ${0} [IMAGE]..."

mkdir -p data

# Use MD5 of first image to name the JSON metadata file
PRIMARY="${1}"

# Avoid posting duplicates
./guard.sh "${PRIMARY}"

HASH=$(md5sum "$PRIMARY" | awk '{print $1}')
JSON_OUT="data/${HASH}.json"

echo "🚀 Starting up..."

# Generate metadata if not already present
if [ ! -f "$JSON_OUT" ]; then
    ./describe.py "$@"
fi

# Interactive editor
./editmeta.py ${JSON_OUT}

# Upload all images under a single identifier
./archive.py "$@"

# Post to bluesky
./bluesky.py "$@"

# Mark deduplication stamp
date > "data/${HASH}"

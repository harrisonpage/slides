#!/usr/bin/env bash
#
# Abort if image has already been posted
#

set -euo pipefail
cd "$(dirname "$0")"

die () {
    echo >&2 "$@"
    exit 1
}

[ "$#" -eq 1 ] || die "Usage: ${0} [IMAGE]"

FILE="$1"
[ -f "$FILE" ] || die "File not found: $FILE"

# Calculate MD5 hash (compatible with macOS and Linux)
HASH=$(md5sum "$FILE" | awk '{print $1}')

# Check for presence of data/<hash>
if [ -f "data/$HASH" ]; then
    echo "Duplicate found: data/$HASH"
    exit 1
fi

exit 0

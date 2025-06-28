#!/usr/bin/env bash

set -e
cd "$(dirname "$0")"

die () {
    echo >&2 "$@"
    exit 1
}

[ "$#" -eq 1 ] || die "Usage: ${0} [IMAGE]"

FILE=${1}
IMAGE="${FILE##*/}"

mkdir -p data

if [ ! -f "data/${IMAGE}.desc" ]; then
    ./describe.py "${FILE}"
fi

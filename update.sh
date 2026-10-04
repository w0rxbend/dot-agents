#!/bin/sh
set -eu
repo=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
git -C "$repo" pull --ff-only
exec python3 "$repo/scripts/manage.py" install "$@"

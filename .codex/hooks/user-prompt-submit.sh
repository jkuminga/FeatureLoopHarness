#!/usr/bin/env sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
exec python3 "$ROOT/.flh/hooks/user_prompt_submit.py"

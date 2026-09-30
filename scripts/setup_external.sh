#!/usr/bin/env bash
# TLDR: Clone or update each external repository into external/<name> at the exact commit pinned in external/deps.lock.json.
# Usage: bash scripts/setup_external.sh [name ...]   (default: every entry). Private repos need GitHub access on the host.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCK="$ROOT/external/deps.lock.json"
names=("$@")
if [ ${#names[@]} -eq 0 ]; then
  mapfile -t names < <(python3 -c "import json;print('\n'.join(k for k in json.load(open('$LOCK')) if not k.startswith('_')))")
fi
for name in "${names[@]}"; do
  url=$(python3 -c "import json;print(json.load(open('$LOCK'))['$name']['url'])")
  commit=$(python3 -c "import json;print(json.load(open('$LOCK'))['$name']['commit'])")
  dest="$ROOT/external/$name"
  if [ ! -d "$dest/.git" ]; then
    git init -q "$dest"
    git -C "$dest" remote add origin "$url"
  fi
  # Fetch just the pinned commit (works for shallow hosts); fall back to a deeper fetch if the server refuses.
  git -C "$dest" fetch -q --depth 1 origin "$commit" || git -C "$dest" fetch -q --depth 500 origin
  git -C "$dest" -c advice.detachedHead=false checkout -q --force "$commit"
  got=$(git -C "$dest" rev-parse HEAD)
  if [ "$got" != "$commit" ]; then echo "PIN MISMATCH for $name: $got != $commit" >&2; exit 1; fi
  echo "$name -> $dest @ $got"
done

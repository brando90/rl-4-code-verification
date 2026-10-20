"""TLDR: Provide deterministic hashing and exclusive durable receipts for v4."""
import hashlib
import json
import os
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def object_digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        if isinstance(value, dict) and 'tldr' in value:
            rest = {k: v for k, v in sorted(value.items()) if k != 'tldr'}
            payload = json.dumps({'tldr': value['tldr'], **rest}, indent=2, allow_nan=False)
            payload = payload.replace('{\n  "tldr"', '{"tldr"', 1)
            stream.write(payload.encode() + b'\n')
        else:
            stream.write(canonical(value) + b'\n')
        stream.flush()
        os.fsync(stream.fileno())

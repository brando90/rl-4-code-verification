"""TLDR: Exact-input asynchronous FSC cache used by experiment09's validated judge transport."""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
from typing import Callable


def request_key(candidate: bytes, reference: bytes, source: bytes, judge_fingerprint: str) -> str:
    """Bind all scientific judge inputs before a cache entry may be reused."""
    h = hashlib.sha256()
    for part in (candidate, reference, source, judge_fingerprint.encode()):
        h.update(len(part).to_bytes(8, "big")); h.update(part)
    return h.hexdigest()


class FSCQueue:
    """Deduplicate only byte-identical logical judge requests; transport remains an injected Valkyrie CLI callback."""

    def __init__(self, root: Path, submit: Callable[[dict], dict], workers: int = 1) -> None:
        if workers < 1:
            raise ValueError("workers must be positive")
        self.root, self.submit = root, submit
        self.root.mkdir(parents=True, exist_ok=True)
        self.pool = ThreadPoolExecutor(max_workers=workers)
        self.pending: dict[str, Future] = {}

    def request(self, payload: dict) -> Future:
        key = request_key(payload["candidate"].encode(), payload["reference"].encode(), payload["source"].encode(), payload["judge_fingerprint"])
        cached = self.root / f"{key}.json"
        if cached.exists():
            done: Future = Future(); done.set_result(json.loads(cached.read_text())["result"]); return done
        if key not in self.pending:
            def run() -> dict:
                result = self.submit(payload)
                if result.get("fsc") is None:
                    raise RuntimeError("validated judge returned no FSC; preserve native error rather than substituting zero")
                tmp = cached.with_suffix(".tmp")
                tmp.write_text(json.dumps({"key": key, "payload_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(), "result": result}, sort_keys=True) + "\n")
                tmp.replace(cached)
                return json.loads(cached.read_text())["result"]
            self.pending[key] = self.pool.submit(run)
        return self.pending[key]

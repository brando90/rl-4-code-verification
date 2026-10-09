"""TLDR: Exact-input asynchronous FSC cache used by experiment09's validated judge transport."""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
import hashlib
import json
import statistics
import threading
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
        self.lock = threading.RLock()

    def request(self, payload: dict) -> Future:
        with self.lock:
            return self._request_locked(payload)

    def _request_locked(self, payload: dict) -> Future:
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


CONFIGS = ('H2_sol_high', 'H2_opus55_max')


def six_rating_result(result: dict) -> dict:
    """Strictly accept all six frozen ratings; a partial median is not FSC."""
    ratings = result.get('ratings', [])
    expected = {(config, repeat) for config in CONFIGS for repeat in (1, 2, 3)}
    observed = [(r.get('config'), r.get('repeat')) for r in ratings]
    if len(ratings) != 6 or set(observed) != expected or len(set(observed)) != 6:
        raise RuntimeError('Missing/duplicate constituent rating: entire FSC batch blocked')
    for rating in ratings:
        score = rating.get('score_raw')
        if (rating.get('status') != 'measured' or type(score) is not int or not 0 <= score <= 5
                or rating.get('prompt_hash_matches') is not True or not rating.get('run_id')):
            raise RuntimeError('Unverified constituent rating: preserve native status; block batch')
    medians = {c: statistics.median(r['score_raw'] for r in ratings if r['config'] == c) for c in CONFIGS}
    value = statistics.fmean(medians.values()) / 5
    if result.get('fsc') is not None and abs(result['fsc'] - value) > 1e-12:
        raise RuntimeError('Reported FSC does not equal the frozen six-rating aggregation')
    costs = [r.get('cost_usd') for r in ratings]
    return {**result, 'fsc': value, 'member_medians': medians,
            'cost_usd': sum(costs) if all(c is not None for c in costs) else None,
            'status': 'measured', 'ratings': ratings}


class BatchFSCQueue:
    """Single-writer asynchronous exact-input queue around a validated CLI batch transport.

    A durable pre-call reservation prevents silent duplicate admission after a
    crash. Recovery adopts recorded transport runs; it must not clear this file
    and reissue calls. Only complete validated six-rating results enter the cache.
    """
    def __init__(self, root: Path, transport: Callable[[list[dict]], dict],
                 max_new_ratings: int, admission_check: Callable[[], None]):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.transport = transport
        self.max_new_ratings = max_new_ratings
        self.admission_check = admission_check
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.lock = threading.Lock()
        self.ledger_path = self.root / 'ledger.json'
        self.ledger = json.loads(self.ledger_path.read_text()) if self.ledger_path.exists() else {'ratings_reserved': 0, 'batches': {}}

    def _write(self, path, value):
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(value, sort_keys=True) + '\n')
        tmp.replace(path)

    def request_many(self, payloads: list[dict]) -> Future:
        # Copy before queuing, so later mutation of a caller's dictionary cannot
        # change the byte-identical inputs under a previously calculated key.
        frozen = json.loads(json.dumps(payloads))
        return self.pool.submit(self._run, frozen)

    def _run(self, payloads):
        with self.lock:
            by_key = {}
            order = []
            for payload in payloads:
                key = request_key(payload['candidate'].encode(), payload['reference'].encode(),
                                  payload['source'].encode(), payload['judge_fingerprint'])
                by_key[key] = {**payload, 'key': key}
                order.append(key)
            accepted, missing = {}, []
            for key, payload in by_key.items():
                path = self.root / f'{key}.json'
                if path.exists():
                    cached = json.loads(path.read_text())
                    if cached['key'] != key or cached['judge_fingerprint'] != payload['judge_fingerprint']:
                        raise RuntimeError('Cache identity mismatch')
                    accepted[key] = six_rating_result(cached['result'])
                else:
                    missing.append(payload)
            if missing:
                self.admission_check()
                batch_id = hashlib.sha256('\n'.join(sorted(p['key'] for p in missing)).encode()).hexdigest()
                previous = self.ledger['batches'].get(batch_id)
                reserved_keys = {key for batch in self.ledger['batches'].values() for key in batch['keys']}
                if previous or reserved_keys.intersection(p['key'] for p in missing):
                    raise RuntimeError(f'Previously reserved batch {batch_id}: adopt recorded runs; never automatically readmit')
                ratings = 6 * len(missing)
                if self.ledger['ratings_reserved'] + ratings > self.max_new_ratings:
                    raise RuntimeError('Fixed constituent-rating budget exhausted')
                self.ledger['ratings_reserved'] += ratings
                self.ledger['batches'][batch_id] = {'status': 'reserved_before_calls', 'ratings': ratings,
                                                  'keys': [p['key'] for p in missing]}
                self._write(self.ledger_path, self.ledger)
                self._write(self.root / f'batch_{batch_id}_inputs.json', missing)
                raw = self.transport(missing)
                self._write(self.root / f'batch_{batch_id}_native_results.json', raw)
                # Validate the entire batch before any cache success is written.
                if set(raw) != {p['key'] for p in missing}:
                    raise RuntimeError('Missing/extra response in judge batch')
                validated = {key: six_rating_result(value) for key, value in raw.items()}
                for payload in missing:
                    key = payload['key']
                    self._write(self.root / f'{key}.json', {'key': key,
                        'judge_fingerprint': payload['judge_fingerprint'], 'result': validated[key]})
                accepted.update(validated)
                self.ledger['batches'][batch_id]['status'] = 'measured_complete'
                self._write(self.ledger_path, self.ledger)
            return [accepted[key] for key in order]

    def close(self):
        self.pool.shutdown(wait=True)

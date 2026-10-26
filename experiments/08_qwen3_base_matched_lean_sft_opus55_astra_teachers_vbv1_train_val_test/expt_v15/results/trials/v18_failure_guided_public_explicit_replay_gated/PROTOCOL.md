# V18 Trial Protocol

The executable V18 source snapshot is in `sources/`. This trial is a fresh, prospectively frozen replay of the admitted V17 curriculum after V17 failed from GPU contention, not a result-bearing continuation of V17.

The start weights are the complete V12-current checkpoint, with a fresh optimizer. Inputs are an exact copy of the V17 verified curriculum: 2,585 original Python-to-Lean rows once and 678 V14 public explicit-proof rows six times. The fixed 135-task validation manifest, eight samples per task, generation settings, and frozen V6 scorer are unchanged. The test split and protected fresh diagnostics remain excluded.

The hypothesis, input hashes, optimizer schedule, allocator gate, retry boundary, evaluation protocol, and success criterion are frozen in `sources/PROTOCOL.md`. The source snapshot, runtime receipt, per-item tables, raw generations, scored cells, and independent terminal receipt remain under this trial/runtime pair.

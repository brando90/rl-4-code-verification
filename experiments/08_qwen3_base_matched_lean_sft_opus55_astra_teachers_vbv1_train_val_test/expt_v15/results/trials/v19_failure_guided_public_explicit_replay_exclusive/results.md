# V19 Results

**Status:** dispatched on October 19, 2026. PID and phase paths are in `manifest.json`; the named tmux session is `rl4cv-v19-public-explicit-exclusive`.

The launcher is currently waiting without a GPU lease because no eligible A100 among GPU 0, 3, 4, 5, and 7 was empty at dispatch. It requires two empty observations 15 seconds apart, then the existing device, E08, and E13 allocator gates. It starts the smoke, the fresh 3,327-update training, frozen 1,080-cell generation, and CPU scoring only after that admission.

V19 has no result until it writes the inherited full validation summary, raw generations, scored cells, and an independent terminal receipt. The target remains unmet at the completed V12-current baseline of 120/1,080 successes (11.11%).

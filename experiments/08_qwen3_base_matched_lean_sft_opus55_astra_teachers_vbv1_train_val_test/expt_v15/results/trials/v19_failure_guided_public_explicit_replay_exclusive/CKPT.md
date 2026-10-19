# V19 checkpoint and frozen-input record

- **Start weights:** `/lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v12/current/run/hf`
- **Start manifest SHA256:** `6b463dee6df652a2e423b2def7570cf95ddcb61c263a1469cec59d3010f71823`
- **Optimizer:** fresh full-parameter AdamW; no V17/V18 model, optimizer, or RNG state is reused.
- **Frozen source inputs:** V12 Python-to-Lean pool SHA256 `6b0cce0608a11b2aa7d31e1343c6db0ba8ade08fdbd62ec68914884064a9df3e` and V14 admission completion SHA256 `810134a605af4c6cfbf4bafa199069cb6c761b79d3149fdec8f2a323482828ed`.
- **Output checkpoint:** populated only after all declared V19 optimizer updates complete at `corpus_training_v19/adapt/run/hf`; interrupted trajectories are never reused.

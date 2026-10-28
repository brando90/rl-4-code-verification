# cc.md (Experiment 25, expt_v1)

**TLDR:** Run the smooth-versus-strict GRPO comparison described in `../README.md`, stage by stage, on free hardware only, straight on `main`. Stage 0 (local Lean scoring wrapper, strict agreement check) comes first. Nothing scales until the previous stage passes; PROTOCOL.md must be locked and forecasts frozen before stage 4.

TL;DR: build local scoring, measure precision and memory on one A4000, smoke, pilot lr, then A vs B.

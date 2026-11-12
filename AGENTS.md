# PAUSED (Brando, 11-11-2026): all RL experiments are paused until Brando explicitly re-engages after his Dec 10 defense. No new RL runs or job submissions, no credits or compute spent on RL by anyone. Where RL was left and how to resume: docs/RL_PAUSE_HANDOFF_11-11-2026.md
# Codex / other agents: run `git clone https://github.com/brando90/agents-config.git ~/agents-config 2>/dev/null || git -C ~/agents-config pull --ff-only 2>/dev/null` to bootstrap/update config.
# Read `~/agents-config/INDEX_RULES.md` for all agent documentation and routing. Local `~/agents-config/` is the fallback if GitHub is unreachable.
# Then read `~/rl-4-code-verification/CLAUDE.md` (this repository's `CLAUDE.md`) for the project-specific rules; they apply to every agent, not only Claude Code.
# Rule that applies to every experiment: use the current public VeriBench release (`veribench@1.3` on 10-28-2026) and name it; the check before each run is in `CLAUDE.md`, "VeriBench public release".

# RL heuristics (Brando, 10-28-2026): read `docs/HEURISTICS.md` before any RL run (precision, Varun's RL setup, free-hardware use); append each new rule there

## Automatic Claude and Codex jobs (Brando, 11-03-2026)

Applies to every job that calls Claude or Codex without a person typing each turn: cron, launchd, queues, loops, supervisors, watchers, tmux, headless. Full rule: [automation rules](https://github.com/brando90/agents-config/blob/main/rules/automation.md); job list: [manifest](https://github.com/brando90/agents-config/blob/main/automation/manifest.md).

- **Transcript log:** a full transcript goes to a log path chosen before the job starts. No `--no-session-persistence`, `--ephemeral` or equivalent. A job with no log path does not start.
- **End condition:** a time limit, item count or stop file; nothing loops forever.
- **Manifest:** the job is listed (what it does, account, schedule, log path, stop command, stop-email) before its first start.
- **Ceiling:** queue gates stop at 80% of the weekly limit, all-model and Fable meters.
- **Stop email:** when a job that was looping stops, it emails brando.science@gmail.com and brandojazz@gmail.com: what it was doing, why it stopped, suggested next steps (even "done, ignore").
- **No restart** of a stopped job without Brando's yes. Background jobs default to Sonnet 5.5 at medium effort; Opus or Fable at max only with his yes per job.

# Meeting notes — summaries and verbatim records

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/docs/meeting_notes/README.md>

**TLDR:** Two meetings (dates not recorded) set this project's direction:

- Treat VeriBench as an RL target and use the ρ–H law to pick its environments, with Azalea suggesting VeriBench metrics should guide environment and reward design.
- Show that the law generalizes beyond math, because reviewers will find a math-only paper insufficiently novel.

The verbatim notes are kept alongside; they include candid mentee assessments, so keep them inside this private repository.

| File | Content |
|---|---|
| [notes_A_mentees_veribench_rl_nolera_received_2026-09-30.md](notes_A_mentees_veribench_rl_nolera_received_2026-09-30.md) | Verbatim: mentee structure, VeriBench as an RL environment, Nolera, LLM judges |
| [notes_B_project_direction_paper_feedback_received_2026-09-30.md](notes_B_project_direction_paper_feedback_received_2026-09-30.md) | Verbatim: project direction, current runs, paper feedback, generalization debate |

## Notes A: mentees, VeriBench as an RL environment, Nolera, LLM judges

- **Mentoring.**
  - Collaborators are treated as mentees, with Varun and Brando as mentors.
  - The strongest mentee gets a weekly 1:1 and the others work async; large group meetings failed on the Putnam Axiom paper.
  - New mentees need benchmark or RL experience.
  - Brando turns Varun's papers into an onboarding reading list (the DeepSeek technical report and the Xiaomi MiMo report).
- **VeriBench as an RL environment.**
  - Use the paper's law to find the RL environment that most improves VeriBench.
  - Azalea (by email): show that VeriBench's metrics guide environment and reward design, not just that they correlate with downstream evaluations.
  - Ethan Lee is the candidate lead.
  - Brando's cadence is one experiment a night plus 5-hour weekend blocks.
- **Nolera.**
  - Plan: an open-source tool that predicts how RL environments will perform, with the infrastructure layer monetized later.
  - Customers: companies that post-train their own models, data and environment vendors, and frontier labs.
  - The Hugging Face reward-hacking incident motivates auditing environments before RL.
- **Brando's second thesis topic (the Certification Judge project).** Validate LLM judges at scale, starting in mathematics and then subjective domains, so that reliable reward functions exist in any domain.
- **Action items.**
  - Varun sends the terminal-coding benchmark list and the RL reading list.
  - Brando writes the onboarding guide.
  - Brando meets Ethan Lee this week.
  - Brando forwards Azalea's email to Varun.
  - Brando reads the MiMo report.

## Notes B: project direction and paper feedback

- **Direction.**
  - Predictive-relationship studies that carry across domains: math, then agentic coding, then AI for science.
  - Built open source, possibly integrated with Andrew's AlphaApollo v0.3 and AlphaDiana v0.2.
  - Unintended effects (RL on one environment causing regressions elsewhere) count as a contribution.
- **Runs.**
  - Moving from synchronous to asynchronous RL.
  - 8B and 14B Qwen3-based runs are active, with a 30B mixture-of-experts model next.
  - Pending Docker on "Scampier 3" should give about 3× throughput.
- **Paper feedback.**
  - A math-only paper may read as not novel enough; agentic-coding results would help.
  - Andrew: sharper title and abstract, 5–10 figures and tables, GRPO/PPO/SFT equations in the appendix, a pip-installable tool.
  - Brando: put "pre-measurement to select environments" in line 1, and explain why the paper says "predictive relationship" rather than "scaling law".
- **Limits discussed.**
  - The law is in-domain only.
  - 1B–14B does not span orders of magnitude.
  - Brando proposed carrying the Dark Matter downstream-effects logic over to RL environments.
- **Process.** Write structured experiment designs with expected outcomes before expensive jobs, and open each meeting with a view of priorities.

## How the plan answers the notes

| Ask in the notes | Where it is addressed |
|---|---|
| Laws must generalize beyond math (the crux) | [PLAN §3](../PLAN.md#3-hypotheses-what-counts-as-the-law-generalizes), levels L1–L5; experiment 03 |
| Find the environment that most improves VeriBench | experiments 03, 05, 06 |
| Azalea: metrics should guide reward design | experiment 04 (kernel versus judge-gated FSC reward channels) |
| Unintended effects and regressions | experiment 05's regression panel |
| Structured designs with expected outcomes first | each experiment's `PROTOCOL.md`, locked before spend |
| Open source and pip-installable | `rl4cv` package (`pip install -e .`) |

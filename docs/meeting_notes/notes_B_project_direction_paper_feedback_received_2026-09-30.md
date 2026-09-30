<!-- TLDR: Verbatim meeting notes (Varun, Andrew, Brando) on the RL-environment project direction, current runs, paper feedback and the generalization debate, as pasted by Brando on 2026-09-30. -->

# Meeting notes B — project direction, experiments and paper feedback (verbatim)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/docs/meeting_notes/notes_B_project_direction_paper_feedback_received_2026-09-30.md>

**TLDR:** Verbatim meeting notes (Varun, Andrew, Brando) on the RL-environment project direction, current runs, paper feedback and the generalization debate, as pasted by Brando on 2026-09-30.

**Provenance:** pasted by Brando into a Claude Code session on 2026-09-30; the meeting date was not given.
The text below is unedited.
Transcription spellings are kept as received; "Brandon" is probably Brando, since the notes attribute the Dark Matter project to "Brando + Rylan" in the same bullet.
Summary and project plan: [README.md](README.md), [../PLAN.md](../PLAN.md).

---

Project Direction and Open Source Vision
   * Goal: build a collection of scaling law studies that generalize across domains
      * Started in mathematics, now expanding to agentic coding, then AI for science
      * Overarching aim: show predictive relationship translates across domains, not just within one
   * Open source framing is central: want GitHub stars, community contributors, domain-specific branches
      * Potential integration with AlphaApollo and AlphaDiana (Andrew’s systems)
      * AlphaApollo v0.3 and AlphaDiana v0.2 releasing this week
   * Unintended effects as a key contribution
      * RL on a specific environment can cause regressions on unrelated benchmarks
      * Example: a bad agentic SWE environment caused downstream cybersecurity sandbox failures
      * Making RL more predictable matters for alignment, not just performance
Current Experiments and Compute Plan
   * Transitioning from synchronous to async RL, aligning with frontier approaches (Xiaomi Mimo, DeepSeek 4.1)
   * Active runs: Nimotron 8B and 14B (Qwen 3 base, instruction fine-tuned, then RL)
      * Next: 30B mixture-of-experts, more representative of frontier scale
   * Study design: replicate scaling relationship in agentic terminal coding, then measure downstream effects on held-out benchmarks (TerminalBench, SWEBench, others)
   * Docker access on Scampier 3 pending: expected to 3x throughput on current VM
Paper Feedback and Positioning
   * Current version is math-domain only; reviewers will likely find this insufficiently novel
      * Math RL environments were common in 2024; not a new setting for the community
      * Agentic coding results would significantly strengthen the novelty claim
   * Andrew’s suggestions:
      * Polish positioning: title and abstract need to excite RL readers immediately
      * Add more figures and tables (currently 3-5; strong RL papers have 5-10)
      * Add appendix coverage of GRPO, PPO, SFT equations for self-containedness (similar to CodeUp paper)
      * Show how findings are usable: open-source tools, pip-installable, generalizable to other settings
   * Brandon’s suggestions:
      * Key insight (“pre-measurement to select environments”) lands on page 1 but not line 1; move it earlier
      * Paper should be explicit that “scaling law” is intentionally avoided in favor of “predictive relationship”
   * Varun’s note: paper was substantially revised post-Sanmi feedback (8:30 PM to 4 AM); main changes were added qualifications, reviewer-proofing claims, expanded appendix, full codebase in submission zip
Scaling Law Scope and Generalization Debate
   * Current law: scales across compute, predicts small-to-large model behavior, but in-domain only
   * Brandon raised Dark Matter project (Brando + Rylan, pre-training era): tested downstream effects of pre-training ablations across orders of magnitude
      * Proposed applying the same logic to post-training / RL environments
   * Model size range (1B to 14B, soon 30B) is not orders-of-magnitude scale; acknowledged as a limitation
   * Andrew’s framing: if the law can save compute and give convincing predictions for university researchers (8-16 GPUs), that is a strong justification
      * Suggested proving generalizability in biology, chemistry, or scientific domains where base models are weak and RL is harder
Process and Design of Experiments
   * Andrew’s key suggestion: translate the plan into concrete, structured experiment designs with expected outcomes before running expensive jobs
   * Brandon echoed: prioritization matters more than generating ideas; bird’s-eye view of priorities needed at the start of each meeting
   * Lab talk proposed: 30-minute presentation to get broader feedback, including from Sanmi’s preference learning class
   * Slides as a working artifact: Andrew suggested putting thoughts directly on slides for async commenting
   * Varun to send meeting notes to Andrew and Brandon via group chat

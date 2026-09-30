<!-- TLDR: Verbatim meeting notes (Varun and Brando) on mentee structure, VeriBench as an RL environment, the Nolera roadmap and LLM-judge thesis work, as pasted by Brando on 2026-09-30. -->

# Meeting notes A — mentees, VeriBench as an RL environment, Nolera, LLM judges (verbatim)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/docs/meeting_notes/notes_A_mentees_veribench_rl_nolera_received_2026-09-30.md>

**TLDR:** Verbatim meeting notes (Varun and Brando) on mentee structure, VeriBench as an RL environment, the Nolera roadmap and LLM-judge thesis work, as pasted by Brando on 2026-09-30.

**Provenance:** pasted by Brando into a Claude Code session on 2026-09-30; the meeting date was not given.
The text below is unedited.
Transcription spellings are kept as received: "VariBench" is VeriBench, and "iClear paper" is the ICLR 2027 submission *Which Environments Should LLMs Learn From? Predicting RL Utility Across Scale*.
Summary and project plan: [README.md](README.md), [../PLAN.md](../PLAN.md).

---

Mentee Structure and Meeting Cadence

* Framing shift: collaborators treated as mentees, not co-equals
   * Varun and Brando are the mentors given publication track record
* Mentee profiles and expected contribution levels:
   * Emily: likely strongest, competitive mathematician
   * Dan: PhD student, meet 1:1 weekly for sure
   * Rakshit: reliable, will attend all meetings, may need more support
   * Ethan Lee: brilliant, creative, competitive programmer; younger, RL background uncertain
* Meeting format: weekly 1:1 with the strongest mentee; others async
   * Group meetings with many collaborators didn’t work well (Putnam Axiom paper lesson)
   * Varun scheduling: Dan on Wednesday, Emily this week, Rakshit TBD

Mentee Onboarding and Quality Bar

* Minimum bar for any new mentee: strong benchmark experience OR RL experience (ideally both)
* Brando to compile a core reading list from papers Varun sends, for all mentees
* Key papers for RL background:
   * DeepSeek technical report
   * Xiaomi MIMO report (already shared in RL Scaling Laws chat)
* Ethan Lee: meet with him this week; Brando to ping him to read the paper in depth

VariBench as an RL Environment

* Core proposal: use the scaling law from the iClear paper to find the optimal RL environment that improves VariBench the most
   * Win for Brando’s thesis, win for reproducibility, win for expanding results in the mathematics domain
* VariBench context: measures a model’s ability to write implementations, proofs, and theorems in formal verification (Lean)
   * Lean is the only formal language with terminal capabilities; others lack this
* Azalea’s suggestion (email confirmed): show how VariBench metrics not just correlate with downstream evals, but guide better environment design and reward functions for RL
* Candidate to lead this work: Ethan Lee (has VariBench familiarity, expressed interest in RL)
* Brando’s cadence: one experiment per night after meetings, 5-hour chunk on weekends

Nolera Roadmap and Revenue Strategy

* Strategy: build the best open-source tool for predicting RL environment performance, then monetize the infrastructure layer
   * Model: Snorkel/Databricks approach with Apache Spark
   * VC interest in strong open-source work; adoption is the current key barrier
* Three target customer segments:
   * Companies post-training their own models (e.g. Harvey): need to predict environment effects before wasting compute
   * Data vendors (Fleet, AfterQuery, Mercur): under scrutiny after Hugging Face incident; environments need auditing
   * Frontier labs: accepting environments with no reliable verification layer
* Hugging Face incident framing: traced to reward hacking from bad cyber environments with no intermediate rewards; agents found test solutions via backend and deleted logs
* Core value proposition: predict how an environment will perform without expensive rollouts; flag and fix bad environments before RL runs
* Moonshot angle: use scaling laws to optimally compose environments for a small model, RL it aggressively across all priority domains, deploy as a fast/cheap enterprise model

Certifying LLM Judges and Domain Expansion

* Brando’s second thesis topic: scalably certifying that an LLM judge is trustworthy
   * Start in mathematics (most verifiable domain), then extend to subjective domains
   * Goal: automatically generate reliable reward functions for any domain
* Connection to Nolera: indirect but significant once extended to non-verifiable domains
   * Example: investment banking, where Goldman vs. Morgan Stanley standards differ; a trustworthy LLM judge unlocks environment design for these domains
* Even the math-only version has commercial value: formal math verification is in demand (Vals, OpenAI Navier-Stokes work)
* Key limitation noted: math verifier quality degrades sharply outside its domain; applicability to economically viable domains still understudied
* Priority domains for Nolera going forward: agentic terminal coding, cybersecurity, AI for science (biology)

Next Steps

* Send Brando the terminal coding benchmark list (Varun)He'll assess overlap with VariBench and consider extensions toward those benchmarks.
* Send Brando the core RL reading list (Varun)Brando will write it up as a structured onboarding guide for all mentees.
* Schedule meeting with Ethan Lee this week (Brando)Ping Ethan to read the iClear paper in depth before the meeting.
* Forward Azalea's email to Varun (Brando)Confirms the VariBench-as-RL-environment direction and her offer to give feedback on results.
* Share Xiaomi MIMO report with Brando (Varun)Already forwarded in chat; Brando to read for environment composition and regression-prevention insights.

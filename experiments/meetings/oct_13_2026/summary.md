# Summary: VeriBench SFT experiments and RL readiness (10-13-2026)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/meetings/oct_13_2026/summary.md>

**TLDR:** A short weekly call (Varun Madan recording; Brando, Ethan "Lethan" Lee and Rakshit Kaushik on the other channel) about the supervised fine-tuning (SFT) warm start that every reinforcement-learning (RL) phase of this project waits on. Brando split ownership of the four Qwen3 Base sizes (Lethan 1.7B and 8B, Rakshit 4B and 14B) under one shared recipe with identical data, order and loss-token budget; Varun confirmed Base models and matched tokens. Two readiness criteria were stated and are different quantities: Varun's RL-signal band of "25 to 75% success rate … running it 8 times", and Brando's performance milestone of "close to 25% accuracy or 25% … SCSC". Mentees bring measured results and a short presentation next time instead of live prompting. Written by Claude Code (`claude-fable-5-1`) on 10-14-2026 from the verbatim [transcript](transcript.md) (sha256 `bb318494…26bd`); the executable records in [experiment 08](../../08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/README.md) settle every size and count.

## How to read this summary

- The transcript is an automatic recording export with two channels: "Me" is Varun Madan, the recorder; "Them" merges Brando, Ethan Lee (Lethan, `@lethan3`) and Rakshit Kaushik (`@rakshit-kaushik`). A quote is attributed to a person only when its content makes the speaker unambiguous; otherwise it is "a participant".
- The automatic transcript garbles names and numbers ("VariBench" for VeriBench, "Quine"/"Quen" for Qwen, "1.67B" for 1.7B, "Open RL" for OpenR1, "SCE" for SCSC, "Coelho lab" for Koyejo lab, "Ratchid" for Rakshit). Numbers quoted below are what was said; the measured values follow from [experiment 08 results](../../08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/results.md).
- Acronyms: SFT (supervised fine-tuning), RL (reinforcement learning), SCSC (Smooth Conjunctive Score for Code verification, the geometric mean of the three VeriBench factor means), MBPP (Mostly Basic Python Problems), SNAP (Stanford Network Analysis Project cluster), B (billion parameters).

## What was discussed

### 1. Opening and status

- Varun opened the call and noted it might run short because of scheduling; the agenda was the open to-dos in the repository.
- Ethan said he had opened the experiments, asked Codex to describe them, and tried to continue experiment 02, but needed Brando's MBPP files and "some other stuff we need to decide".
- Rakshit said he had not yet started: "I'll get to it after my midterm tomorrow … push some updates by like the afternoon tomorrow, like by Friday, asynchronously on the group." This is an intention, not an agreed deadline.
- Several minutes went to the missing MBPP file: Brando believed his agent had emailed it, possibly to the wrong Ethan ("there's 2 Ethans"), or that a Stanford mail restriction on attachments had dropped it ("this is a JSONL, not zip though"). See [action_items.md](action_items.md) for the post-meeting resolution.

### 2. Brando's high-level framing of the project

Brando described two ideas, screen-sharing his experiments folder:

1. **Use the ρ–H predictive law to choose or generate environments for a specific benchmark.** Varun clarified the intent: "Generating types of environments, but it's very much to select the best one … you can also grab environments that you find that would be suitable for VeriBench … It just needs to be measurable and within the properties that we need to create the scaling laws."
2. **Azalia's feedback on the factorized metric.** Brando explained that VeriBench's metric decomposes code verification into skills (docstrings, implementation, tests, formal specifications, which are unproved theorem statements, and proved theorems), aggregated by a geometric mean as a "smooth AND". Azalia suggested demonstrating that this decomposition raises the preferred downstream metric (pass@1 or accuracy). Varun: "I think that could totally be something cool." Brando's reading: factor scores correlated with pass@1 could make model improvement interpretable ("you know it's not good at, say, the docstrings or the theorem writing").

### 3. The warm start: what the agent reported, and what the records say

Brando recalled that Varun had said RL needs a warm-up SFT model, that the Base model "didn't work", and that Varun had said not to use the Instruct model because the comparison "wasn't apples to apples". He then read his agent's report of experiment 08 aloud.

- Transcript reading: "the SFT on the teacher-written Lean files lifted Qwen 8B to 0.12 on the VeriBench V1 test split from 0 … the 1.7B on the validation … failed the format gates", followed by garbled numbers "0.8, 0.1, and 0.087" and "I'm surprised that the 14B did worse … I don't know if it's within the confidence interval."
- Measured record ([results.md](../../08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/results.md), test split, 222 tasks × 8 samples, 1,776/1,776 known cells per system, 95% task-bootstrap intervals from 10,000 resamples, seed 0, p-val=n/a): selected 8B at step 658 has SCSC **0.1116 [0.0823, 0.1435]** versus Base 8B 0.0000 [0.0000, 0.0000]; selected 14B at step 334 has **0.0869 [0.0651, 0.1095]** versus Base 14B 0.0023 [0.0004, 0.0045]. The 14B checkpoint trained on half the loss tokens of the 8B one (2,884,708 versus 5,752,936), so the "14B did worse" comparison is unmatched, as the experiment's own verdict states. Experiment 08 version 2 was to evaluate all sizes at step 658; it is route-blocked (see action items).
- Validation record (135 tasks × 8 samples per rung; frozen gates: extraction ≥ 972/1,080, capped ≤ 108/1,080, mixed-success tasks ≥ 7/135; p-val=n/a): 8B step 658 and 14B step 334 pass; 1.7B and 4B pass no rung, and their final checkpoints miss both formatting gates (1.7B: 897 extracted / 184 capped; 4B: 946 / 134, each of 1,080).
- Ethan's hypothesis: "it kind of sounds like it's just not producing valid output, like malformed JSON or something." Varun agreed it "might be a misconfiguration of the model settings or the JSON outputs." The harness extracts Lean files from text, so this is a diagnosis to test, not an established cause (see [PLAN.md](PLAN.md)).

### 4. Matched recipe, confirmed

Brando dictated to his agent: "make sure to finish the 1.7B and 4B and fully test it. Crucial that all the models are SFT'd on the same data and same number of tokens, right, Varun?" Varun: "Yes." Brando: "we should also do the same number of steps, right, Varun? Or I guess it depends on the context length." Varun: "Same number of tokens. Yes." Brando: "Whatever that means for batch length, context length, et cetera." The record already satisfies this at version 1: all four sizes ran 658 updates and 5,752,936 loss tokens on the same 1,315 examples from 476 of 539 train tasks.

### 5. The two readiness criteria (different quantities)

Brando asked Varun: "how would I know if the performance improved enough such that it's worth doing RL experiments now?"

- **Varun's RL-signal band:** "You're aiming for around 25 to 75% success rate, I would argue … And this is running it like 8 times on that model. If it can't do that, then we have to update the fine-tuning. Slash up the size." This is a binary success rate per task over 8 attempts; it describes whether groups are mixed enough for RL to learn.
- **Brando's performance milestone**, stated later while briefing Rakshit: "produce a model that has close to 25% accuracy or 25% … SCSC, which is the metric that we use for VeriBench … when you don't SFT, that score is 0 … I managed to get like 0.1 … we need just 10 more points, probably we just need to increase the data size a little bit more." He added: "I suppose that if it's 10%, we can try RL and see if it works, but the lower the number, the more risk there is."

These are not the same quantity. SCSC is the geometric mean of three factor means on one measured cohort, so an SCSC of 0.25 is not a 25% probability of success, and a pooled success rate does not show that most tasks fall in the 25–75% band. The folder's [PLAN.md](PLAN.md) keeps both visible, assessed on the validation split only: at the shared full budget, binary success is 0.0963 [0.0630, 0.1343] for 8B and 0.1204 [0.0833, 0.1620] for 14B (135 tasks × 8 attempts, 95% task-bootstrap intervals, 10,000 draws, one training seed, p-val=n/a). The SCSC milestone has not been measured on the validation ladder.

### 6. Ownership

Brando: "since we have 4 sizes … Ethan can do like 1.7B and 8B. And Rakshit, you can do the other 2, the 4B and 14B … probably the 8B and the 14B are easier to make work, like Varun mentioned." Rakshit asked whether everyone should use "the same sort of environment and everything for all the models"; Brando answered that there is no environment yet and the SFT warm start comes first, which Varun confirmed. Ownership of a size does not authorize a separate recipe: both owners consume one frozen corpus, order and token schedule ([PLAN.md](PLAN.md)).

### 7. Data sources

- **OpenR1.** Varun asked whether the "original WarmStart OpenR1 data" had been tried for the SFT. Brando: "that's not Lean data … there's no natural language in Lean, so I don't know if it'll help." Varun: "then fine-tune with Lean because it should understand the formatting of whatever it's trying to RL on. So yeah, I agree." OpenR1 math-only SFT is therefore a lower-priority alternative.
- **Python-to-Lean teacher data.** Brando described the recipe used so far: have a frontier model translate open-source Python files to Lean, "make sure to only train on data that compiles", "try to complete proofs", then SFT on that translation. He said mentees "can use the Coelho [Koyejo] lab keys like the Stanford or the Vals keys" to produce such data. For runs Brando or his agents execute, decision D-108 (Vals Valkyrie) governs; collaborators use their own authorized access ([CLAUDE.md](../../../CLAUDE.md), "Compute and model calls").
- **The benchmark is the test set.** Rakshit asked whether the website's Python files were the SFT source. Brando: "No, no, no. The website has the benchmark. So that's the test set … Don't train on the test set." The repository's split (train 539 / validation 135 / test 222, D-013) is the executable form of this rule.
- **VeriBench-Infinity.** A participant said: "we have like a huge source of like correct Lean data from the VeriBench Infinity that I was doing before." Brando: "Ah, yeah." No decision was taken; it is a candidate source only after its source tasks are identified and disjointness from validation/test is shown ([PLAN.md](PLAN.md), "Data and execution contract").
- Brando pointed to the VeriBench data format; the repository's [format guide](../../../docs/veribench_data_format/README.md) is the written version.

### 8. Compute access

Rakshit asked whether mentees have compute. Brando: SNAP; "email the IT, CC me and Eric Pineda". Ethan had already sent such an email and was asked to CC Rakshit.

### 9. Meeting format going forward

Brando: "I don't think it's the best use of time for me to prompt the models live and explain it … next time let's just do this beforehand and you guys tell me, present to us what the results were." Ethan and Rakshit: "Agreed, agreed."

### 10. Close

Varun had to leave and promised to send the automatic meeting notes. The transcript in this folder is that record (committed in `aad3719`, 10-13-2026 18:09 PDT).

## Decisions recorded

Carried into [docs/DECISIONS.md](../../../docs/DECISIONS.md) as D-017 and into [docs/PLAN.md](../../../docs/PLAN.md) § 12:

1. Lethan owns 1.7B and 8B; Rakshit owns 4B and 14B; one shared recipe with identical SFT examples, order and loss-token budget at every size.
2. Base models, never Instruct.
3. Readiness is assessed on the validation split with both criteria visible: Varun's 25–75% success at 8 attempts (mixed groups) and Brando's SCSC ≥ 0.25 milestone.
4. Mentees bring measured results and a short presentation to the next meeting.
5. OpenR1 math-only SFT is a lower-priority alternative; Lean data is needed.
6. VeriBench-Infinity is a candidate Lean source only after source-task identification and a disjointness proof against validation and test.
7. Keys suggested in the meeting do not override D-108 for Brando's runs.

## What the meeting did not settle

- No deadline: "tomorrow" and "Friday" were Rakshit's intentions around a midterm.
- No fix for the 1.7B/4B failures; the "malformed JSON" explanation is a hypothesis.
- No decision on VeriBench-Infinity or on more teacher generation.
- Whether 14B is worse than 8B after matched training remains unknown until experiment 08 version 2 runs; it is blocked by the Vals Valkyrie route (HTTP 403 since 10-13-2026 03:27 PDT).

**TL;DR:** The warm start is the dependency; it is split by size between Lethan and Rakshit under one recipe, judged on validation by two distinct criteria (Varun's 25–75% success at 8 attempts; Brando's SCSC ≥ 0.25), and the next meeting is results-first.

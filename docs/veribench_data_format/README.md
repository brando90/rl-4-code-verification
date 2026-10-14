# Creating data in the VeriBench format

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/docs/veribench_data_format/README.md>

**TLDR:** Start with a Python program and produce a complete Lean 4 file: implementation, executable tests, meaningful specifications, proved theorems, and an imperative implementation with a proved equivalence where applicable. Use the browsable addition pair below to learn the structure, then choose properties that characterize your own program. Format alone does not make an example correct or eligible for training.

**Read the Python and Lean examples side by side.**

| Start here | What you learn |
|---|---|
| [Python source and tests](examples/py_src/my_add.py) | The behavior to translate, accepted inputs, and example tests |
| [Complete Lean file](examples/lean_src/my_add.lean) | The ordered sections, property declarations, actual proofs, and imperative equivalence |
| [Original downloadable archive](vb_cononical_examples_py_lean.zip) | The supplied bundle, preserved byte for byte, including its original filename |
| [Provenance and hashes](provenance.json) | Where the files came from and how to verify exact copies |
| [Verification receipt](verification.json) | Executed checks, toolchain, and their observed results |

These are copies of VeriBench's existing addition example, provided here for contributors. They are not a newly admitted training corpus or a change to the benchmark's gold references. This guide covers the single-file Python-to-Lean format used by **VeriBench V1**, the original benchmark; the private multi-file version and VeriBench-Infinity have separate task packaging.

**A complete Lean response contains the following sections in order.**

| Order | Section | What to write | Where to look in the addition example |
|---|---|---|---|
| 1 | Module documentation | Name the task, describe the modeled behavior, and list the sections | Opening `/-! ... -/` comment |
| 2 | Functional implementation | A faithful Lean definition, with a short explanation and examples | `myAddNonNegative` |
| 3 | Executable tests | Basic, boundary, positive, negative, and representative property cases | `example` declarations and `#eval` commands |
| 4 | Precondition | A `Prop` describing the valid input domain | `Pre` |
| 5 | Properties and proved theorems | Named propositions about the implementation, each with a proof | `right_identity_prop` / `right_identity_thm`, and the other pairs |
| 6 | Postcondition | A conjunction of the properties the implementation must satisfy | `Post_prop` |
| 7 | Correctness theorem | Prove that the precondition implies the postcondition | `correctness_thm` |
| 8 | Imperative implementation | The corresponding stateful or loop-based implementation, when applicable | `myAddNonNegativeImp`, using `Id.run do` |
| 9 | Imperative tests | Check the corresponding concrete cases | The second test suite |
| 10 | Equivalence theorem | Prove agreement between the functional and imperative versions | `myAddNonNegative_equivalence_thm` |

Keep a task-specific namespace and its closing `end`. The upstream curation guide counts nine sections by grouping imperative tests with the imperative implementation; it describes the same structure. Match the assigned task contract: a full imperative example needs its tests and equivalence proof, while a task with no applicable imperative form needs an explicit explanation rather than an invented implementation.

For example, this actual excerpt connects a property to a proved theorem:

```lean
def right_identity_prop (n : Nat) : Prop := myAddNonNegative n 0 = n

@[simp] theorem right_identity_thm (n : Nat) : right_identity_prop n := Nat.add_zero n
```

The proposition states the requirement. The theorem supplies evidence that it holds for every natural number, rather than just a few test inputs.

**Preserve the source program's behavior and explain any abstraction.**

Choose types, preconditions, return values, and failure behavior from the source. Do not replace an algorithm with an easier function merely because the latter is easier to prove. Address empty inputs, bounds, integer signs, overflow, mutation, and error cases when the source makes them relevant.

The addition pair illustrates an important limitation. Python accepts non-negative integers and raises `ValueError` outside its accepted domain; Lean's `Nat` type represents natural numbers, so negative inputs cannot be supplied. The Lean example models valid-domain addition, not Python's runtime exception behavior. State such domain choices explicitly in new data; use an explicit result or error type if rejection behavior is part of the target specification.

The preserved Python module docstring says `AssertionError`, but the implementation and negative tests use `ValueError`. Follow executable behavior when explaining this example. Also, Python's `isinstance(x, int)` accepts booleans: if your new task intends to exclude them, state and implement that choice rather than assuming it.

**Write specifications that constrain the program, then prove them.**

The upstream curation guide asks for at least three semantically distinct properties. Choose properties that capture the task's behavior, rather than repeating concrete tests under theorem names. For sorting, relevant obligations might include sorted output and preservation of input elements; for a safe access check, they might describe both accepted and rejected requests. Only assert properties the actual program satisfies.

Use this completeness check in each candidate's manifest as `comprehensiveness_note`: what does the function do, what behavior do the theorems establish, and what specified behavior remains unproved or unmodeled? More theorem names do not imply broader coverage. Do not invent inverse functions or artificial input cases to satisfy a count.

- Prove every named theorem, including correctness and applicable equivalence. An unfinished `sorry` or `admit` is not a completed training target.
- Use `native_decide` only for anonymous `example` tests. Named theorems must pass the kernel dependency check with only `propext`, `Classical.choice`, and `Quot.sound` allowed.
- Reject postconditions and properties that say only `True`, a self-equality, or something unrelated to the implementation. `Pre := True` can be legitimate when the function's guarantees hold for every input.
- When a property changes, update its proof, `Post_prop`, and the correctness theorem together.

Compilation, passing tests, and proved theorems answer different questions. A compiled file can still contain unfinished proofs, and a proved weak statement can still miss the intended behavior. Formal specification coverage measures the latter issue through the project's validated judge; do not treat a compile result as a coverage score.

**Verify the files with the pinned Lean toolchain.**

From the root of this repository, the supplied pair can be checked without additional Lean packages:

```bash
python3 docs/veribench_data_format/examples/py_src/my_add.py
lean +leanprover/lean4:v4.22.0 docs/veribench_data_format/examples/lean_src/my_add.lean
```

The `+leanprover/lean4:v4.22.0` argument selects the pinned toolchain through `elan`, Lean's version manager. For a new file that imports the benchmark's dependencies, first follow the existing [external dependency setup](../../README.md#quick-start), then run it in the benchmark project:

```bash
cd external/veribench/veribench_dataset/lean_src
lake env lean /absolute/path/to/your_task.lean
```

Also inspect every named theorem's dependencies using `#print axioms YourNamespace.your_theorem` in a temporary copy, and run the project's kernel verifier when admitting data. Record the compiler version, exit status, file hashes, theorem dependencies, tests, semantic checks, and any omitted behavior. The [receipt](verification.json) records checks on this exact supplied pair; it does not establish correctness of a future example.

**Package source files separately from the training conversation.**

For contributor handoff, pair `py_src/<task>.py` with `lean_src/<task>.lean` under the same stable task identifier. Include a manifest with source and license provenance, family, source-group identifier, file hashes, `comprehensiveness_note`, and validation results. Keep related variants in one source group so they cannot leak across data splits. New raw corpora belong on the execution host; commit manifests and summaries under the repository's existing data policy.

For **supervised fine-tuning (SFT)**, this repository's existing [matched-training assembler](../../experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/scripts/assemble_sft_e08.py) writes **JSON Lines (JSONL)**, one JSON object per line. Its row contains `index`, `task_id`, `teacher`, `r`, `order_key`, and a `messages` list with system, user, and assistant roles. The user message contains the task prompt and Python source; the assistant message contains the complete response in the exact envelope expected by that experiment's extractor.

Use the active prompt builder, extractor, and tokenizer template when converting data. Preserve the assistant response verbatim and check that extracting it recovers the intended Lean file. Verify which tokens receive training loss and enforce the declared length limit. Do not simply rename an older `lean` field to `messages`, add invented reasoning, or assume plain Lean text and an encoded response are interchangeable.

**Check split eligibility before admitting any example to training.**

VeriBench V1's current split contains 539 train, 135 validation, and 222 test tasks. Only train tasks and their authorized references are eligible for training under that split; validation selects checkpoints and test is held out. Older locked experiments retain their stricter exclusions. These documentation examples do not grant training eligibility to copied benchmark material.

Run the exact-hash and near-duplicate screens in [the dataset policy](../DATASETS.md#contamination-and-integrity-screens-required-before-any-pool-is-used) against the protected splits and other held-out panels. Screen the complete rendered content, preserve related-task groups, and record rejected examples. External HumanEval-derived material remains excluded; use the policy's explicit distinction for already assigned VeriBench train tasks.

For a new or changed **benchmark gold reference**, follow the existing strongest-tier Claude and Codex acceptance requirement and upstream curation process. Copying these existing examples for documentation does not replace that acceptance process.

**Use the source contracts when a task needs more detail.**

- [VeriBench section order and proof requirements](https://github.com/brando90/veribench/blob/821d0819589846c232f13457019ae5880198d80a/docs/agent_rules/lean_format_and_gold_references.md)
- [Upstream example curation guide](https://github.com/brando90/veribench/blob/821d0819589846c232f13457019ae5880198d80a/veribench_dataset/instruction_creating_examples_and_curating.md), including the comprehensiveness note. Its older theorem-level `native_decide` suggestions are superseded by the proof requirements above.
- [Lean setup and compilation](https://github.com/brando90/veribench/blob/821d0819589846c232f13457019ae5880198d80a/docs/agent_rules/lean_setup_and_verification.md)
- [Current project rules](../../CLAUDE.md), [dataset admission policy](../DATASETS.md), and [the meeting's shared training plan](../../experiments/meetings/oct_13_2026/PLAN.md)

**TLDR-end:** [rl4cv: VeriBench data format guide] Create complete Python-to-Lean examples with behavior-specific proved properties, tests, preconditions, postconditions, and applicable imperative equivalence. Verify the exact files and data eligibility before using them for training or proposing them as benchmark references.

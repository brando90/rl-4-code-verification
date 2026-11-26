# Open code-verification issues and PRs, anarres-organization/anarres (dated 2026-11-25)

| Issue | What it asks | Who is on it (source) | Still open (as of Nov 25 2026, 10:50 AM) | My action |
|---|---|---|---|---|
| #24 Measure a capable policy repeatedly on development tasks | Repeated measurement of one contained policy on Vero development tasks | Sri (Srivatsava): released as PR #98, merged 37b279b; Sri's comment of Nov 25 00:43 says the readiness gate passes ("decision: ready"); leaves closing to a maintainer | Maintainer review and closing; next frozen protocol must fix two hash-pinned items (native_decide rule, trusted-axiom closure); native-configuration rerun with a Sol-matched budget and open-model screens (Sri: "next step") | Not duplicated |
| #25 Design and freeze a prospective panel | Outcome-blind candidate panel on one proof language | Nobody; no branch or PR found | Blocked: Sri's Nov 24 note says Sol is hosted and cannot be trained, so a trainable starting policy measured under the same contract is needed first | Not started (blocked) |
| #26 Execute and score the frozen panel | Train every frozen candidate, score the frozen decision | Nobody | Blocked behind #25 | Not started (blocked) |
| #27 Track formal verification to a prospective test | Program tracker | Varun (author); Sri's Nov 24 status comment says its Current state section is out of date | Tracker text still says Sol did not pass containment | Nothing to implement (issue says so) |
| #65 Qualify sources, select next transfer test | Four or five sources, proceed/reserve/reject | Sri (assignee). PR #99 merged c148d70; outcome abstain, all five in reserve, Vero leading | Still owed per Sri: five-arm matched-exposure panel draft; one complete source-to-verifier-to-outcome trace; recommended smoke tests (OSS Verify replay, VeruSAGE-Bench) | Not duplicated |
| #66 Portable formal-verification CLI | Source, verifier and runner interfaces; fixture path; Vero byte-stable | Nobody on GitHub: no assignee, no comments, no branch or PR in the repo or in lindicaphxag-tech's fork. Varun's Nov 17 Discord post named #66 as a starting point for Dan, Sri and lethan3; Sri's Nov 24 note says "not started". Brando's Nov 23 Discord question (keep #66 Lean-only first) has no reply | Everything | Taking its first PR (below) |
| #11 CyberGym measurement as adapter evidence | Machine-readable evidence plus status/verify in the vulnerability adapter | lindicaphxag-tech: comment of Nov 23 06:19 says task-level rollouts are not released and asks the maintainers to pick option 1 or 2; a branch contrib/cybergym-released-evidence exists in their fork | Answer from a maintainer; rollouts not public | In flight, not duplicated. Cyber, not formal verification |
| #71 Versioned installable adapters | Package distribution | Nobody | Everything | Not code verification (distribution of all adapters); left alone |


## Open pull requests checked (read 2026-11-25 12:40 PST, 8 open)

| PR | Author | Topic | Code verification? |
|---|---|---|---|
| #82 | lindicaphxag-tech | Verifier reliability pilot, mathematics domain (false-negative tolerance, seed spread) | No: math verifier study; touches tools/check_study_reproduction.py only |
| #83 | lindicaphxag-tech | Portable robotics adapter (RFC 0007, first stage of #64) | No: robotics; touches no Rust file this work touches |
| #90 | AndrewZhou924 | macOS CLI validation report | No |
| #91, #93 | AndrewZhou924 | Surrogate-model research proposals (#92, #94) | No |
| #95, #96, #97 | lindicaphxag-tech | Cyber qualification laws (grouping, information floor, early stopping) | No: cyber |

The formal-verification PRs #98, #99, #100 and #101 are all merged (main is d168e2a, #101). No open pull request carries code-verification work, so nothing was duplicated.

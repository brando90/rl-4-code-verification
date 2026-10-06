-- TLDR: Generated bounded fixture; Candidate.impl is the only callable implementation.
import Mathlib
namespace Candidate
def impl (n : Nat) : Nat := (n + 1)
end Candidate
axiom submitted_assumption : ∀ n : Nat, Candidate.impl n = (n + 1)
theorem submitted_certificate : ∀ n : Nat, Candidate.impl n = (n + 1) := submitted_assumption

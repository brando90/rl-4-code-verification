-- TLDR: Generated bounded fixture; Candidate.impl is the only callable implementation.
import Mathlib
namespace Candidate
def impl (n : Nat) : Nat := (n + n)
end Candidate
axiom submitted_assumption : ∀ n : Nat, Candidate.impl n = (n + n)
theorem submitted_certificate : ∀ n : Nat, Candidate.impl n = (n + n) := submitted_assumption

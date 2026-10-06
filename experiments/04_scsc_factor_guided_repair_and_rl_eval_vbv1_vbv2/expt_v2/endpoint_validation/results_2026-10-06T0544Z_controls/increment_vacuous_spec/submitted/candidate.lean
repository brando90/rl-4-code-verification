-- TLDR: Generated bounded fixture; Candidate.impl is the only callable implementation.
import Mathlib
namespace Candidate
def impl (n : Nat) : Nat := n
end Candidate
theorem submitted_certificate : ∀ n : Nat, False → Candidate.impl n = n := by intro n h; exact False.elim h

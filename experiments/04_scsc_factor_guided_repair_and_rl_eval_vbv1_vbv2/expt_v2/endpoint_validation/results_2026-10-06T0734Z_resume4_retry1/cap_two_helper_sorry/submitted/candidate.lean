-- TLDR: Generated bounded fixture; Candidate.impl is the only callable implementation.
import Mathlib
namespace Candidate
def impl (n : Nat) : Nat := (min n 2)
end Candidate
theorem submitted_helper : ∀ n : Nat, Candidate.impl n = (min n 2) := by sorry
theorem submitted_certificate : ∀ n : Nat, Candidate.impl n = (min n 2) := submitted_helper

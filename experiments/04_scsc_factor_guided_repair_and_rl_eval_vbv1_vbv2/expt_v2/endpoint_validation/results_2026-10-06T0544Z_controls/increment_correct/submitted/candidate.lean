-- TLDR: Generated bounded fixture; Candidate.impl is the only callable implementation.
import Mathlib
namespace Candidate
def impl (n : Nat) : Nat := (n + 1)
end Candidate
theorem submitted_certificate : ∀ n : Nat, Candidate.impl n = (n + 1) := by intro n; rfl

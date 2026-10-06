-- TLDR: Generated bounded fixture; Candidate.impl is the only callable implementation.
import Mathlib
namespace Candidate
def impl (n : Nat) : Nat := n
end Candidate
theorem submitted_certificate : ∀ n : Nat, Candidate.impl n = (n + n) := by intro n; rfl

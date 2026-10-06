-- TLDR: Generated bounded fixture; Candidate.impl is the only callable implementation.
import Mathlib
namespace Candidate
def impl (n : Nat) : Nat := n
end Candidate
theorem reference_obligation : ∀ n : Nat, Candidate.impl n = (n + 1) := by intro n; simp [Candidate.impl]; omega

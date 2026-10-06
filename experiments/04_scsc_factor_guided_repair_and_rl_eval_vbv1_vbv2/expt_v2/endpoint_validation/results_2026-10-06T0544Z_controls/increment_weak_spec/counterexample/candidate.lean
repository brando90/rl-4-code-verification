-- TLDR: Generated bounded fixture; Candidate.impl is the only callable implementation.
import Mathlib
namespace Candidate
def impl (n : Nat) : Nat := n
end Candidate
theorem reference_counterexample : Candidate.impl 0 ≠ 1 := by decide

-- TLDR: Generated bounded fixture; Candidate.impl is the only callable implementation.
import Mathlib
namespace Candidate
def impl (n : Nat) : Nat := (n + n)
end Candidate
theorem reference_test_0 : Candidate.impl 0 = 0 := by decide
theorem reference_test_1 : Candidate.impl 1 = 2 := by decide
theorem reference_test_2 : Candidate.impl 2 = 4 := by decide
theorem reference_test_3 : Candidate.impl 7 = 14 := by decide

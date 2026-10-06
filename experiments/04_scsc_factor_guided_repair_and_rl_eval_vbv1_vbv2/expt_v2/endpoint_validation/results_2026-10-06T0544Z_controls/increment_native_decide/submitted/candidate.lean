-- TLDR: Generated bounded fixture; Candidate.impl is the only callable implementation.
import Mathlib
namespace Candidate
def impl (n : Nat) : Nat := (n + 1)
end Candidate
theorem submitted_certificate : Candidate.impl 0 = 1 := by native_decide

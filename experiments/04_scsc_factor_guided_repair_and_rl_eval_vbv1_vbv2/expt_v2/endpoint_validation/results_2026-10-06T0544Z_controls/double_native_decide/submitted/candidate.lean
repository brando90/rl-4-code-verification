-- TLDR: Generated bounded fixture; Candidate.impl is the only callable implementation.
import Mathlib
namespace Candidate
def impl (n : Nat) : Nat := (n + n)
end Candidate
theorem submitted_certificate : Candidate.impl 0 = 0 := by native_decide

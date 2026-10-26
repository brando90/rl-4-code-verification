import Mathlib
namespace Tiny
def solution (p : Bool) : Int := if p then 1 else 0
theorem spec_nonnegative (p : Bool) : 0 <= solution p := by
  cases p <;> norm_num [solution]
theorem test_true : solution true = 1 := by decide
theorem test_false : solution false = 0 := by decide
end Tiny

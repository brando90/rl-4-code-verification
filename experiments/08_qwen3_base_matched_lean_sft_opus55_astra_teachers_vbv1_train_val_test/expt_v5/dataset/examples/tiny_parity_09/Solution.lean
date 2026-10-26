import Mathlib
namespace Tiny
def solution (x : Int) : Bool := (-x) % 2 == 0
theorem spec_double_neg (x : Int) : solution (-x) = solution x := by simp [solution]
theorem test_even : solution 6 = true := by decide
theorem test_odd : solution (-3) = false := by decide
end Tiny

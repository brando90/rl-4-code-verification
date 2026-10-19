import Mathlib
namespace Tiny
def solution (x : Int) : Bool := |x| % 2 == 0
theorem spec_neg (x : Int) : solution (-x) = solution x := by simp [solution]
theorem test_even : solution (-8) = true := by decide
theorem test_odd : solution 5 = false := by decide
end Tiny

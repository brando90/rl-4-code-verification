import Mathlib

namespace Tiny

def solution (x y : Int) : Int := abs (x - y)

theorem spec_nonnegative (x y : Int) : 0 ≤ solution x y := by
  exact abs_nonneg (x - y)

theorem test_increasing : solution 2 7 = 5 := by norm_num [solution]
theorem test_decreasing : solution 7 2 = 5 := by norm_num [solution]

end Tiny
#print axioms Tiny.spec_nonnegative
#print axioms Tiny.test_increasing
#print axioms Tiny.test_decreasing

import Mathlib

namespace Tiny

def solution (x y : Int) : Int := max (-x) (-y)

theorem spec_left_le (x y : Int) : -x ≤ solution x y := by
  exact le_max_left (-x) (-y)

theorem test_first : solution 2 7 = -2 := by norm_num [solution]
theorem test_second : solution (-3) 1 = 3 := by norm_num [solution]

end Tiny
#print axioms Tiny.spec_left_le
#print axioms Tiny.test_first
#print axioms Tiny.test_second

import Mathlib

namespace Tiny

def solution (x y : Int) : Int := min (-x) (-y)

theorem spec_le_left (x y : Int) : solution x y ≤ -x := by
  exact min_le_left (-x) (-y)

theorem test_first : solution 2 7 = -7 := by norm_num [solution]
theorem test_second : solution (-3) 1 = -1 := by norm_num [solution]

end Tiny
#print axioms Tiny.spec_le_left
#print axioms Tiny.test_first
#print axioms Tiny.test_second

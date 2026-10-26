import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := min (x + z) (y + z)

theorem spec_le_left (x y z : Int) : solution x y z ≤ x + z := by
  exact min_le_left (x + z) (y + z)

theorem test_left_smallest : solution 2 7 (-3) = -1 := by norm_num [solution]
theorem test_right_smallest : solution 7 2 (-3) = -1 := by norm_num [solution]

end Tiny
#print axioms Tiny.spec_le_left
#print axioms Tiny.test_left_smallest
#print axioms Tiny.test_right_smallest

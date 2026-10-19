import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := min (max x y) (max x z)

theorem spec_le_left (x y z : Int) : solution x y z ≤ max x y := by
  exact min_le_left (max x y) (max x z)

theorem test_common : solution 2 7 3 = 3 := by norm_num [solution]
theorem test_first : solution 9 7 3 = 9 := by norm_num [solution]

end Tiny
#print axioms Tiny.spec_le_left
#print axioms Tiny.test_common
#print axioms Tiny.test_first

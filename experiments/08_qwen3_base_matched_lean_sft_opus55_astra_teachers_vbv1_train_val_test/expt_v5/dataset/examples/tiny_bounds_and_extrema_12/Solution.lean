import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := max (x + z) (y + z)

theorem spec_left_le (x y z : Int) : x + z ≤ solution x y z := by
  exact le_max_left (x + z) (y + z)

theorem test_left_largest : solution 7 2 (-3) = 4 := by norm_num [solution]
theorem test_right_largest : solution 2 7 (-3) = 4 := by norm_num [solution]

end Tiny

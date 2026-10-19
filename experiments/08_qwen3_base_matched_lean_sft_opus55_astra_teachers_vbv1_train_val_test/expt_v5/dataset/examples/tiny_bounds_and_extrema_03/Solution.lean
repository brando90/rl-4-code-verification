import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := min (min x y) z

theorem spec_le_first (x y z : Int) : solution x y z ≤ x := by
  exact le_trans (min_le_left (min x y) z) (min_le_left x y)

theorem test_last_smallest : solution 3 2 (-1) = -1 := by norm_num [solution]
theorem test_first_smallest : solution (-4) 2 1 = -4 := by norm_num [solution]

end Tiny

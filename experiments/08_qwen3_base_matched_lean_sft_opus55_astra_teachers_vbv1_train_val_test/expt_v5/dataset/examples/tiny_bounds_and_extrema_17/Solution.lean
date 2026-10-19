import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := min x (max y z)

theorem spec_le_first (x y z : Int) : solution x y z ≤ x := by
  exact min_le_left x (max y z)

theorem test_first : solution 2 7 3 = 2 := by norm_num [solution]
theorem test_inner : solution 9 7 3 = 7 := by norm_num [solution]

end Tiny

import Mathlib

namespace Tiny

def solution (x y : Int) : Int := max (abs x) (abs y)

theorem spec_left_le (x y : Int) : abs x ≤ solution x y := by
  exact le_max_left (abs x) (abs y)

theorem test_first : solution (-2) 7 = 7 := by norm_num [solution]
theorem test_second : solution (-8) 3 = 8 := by norm_num [solution]

end Tiny

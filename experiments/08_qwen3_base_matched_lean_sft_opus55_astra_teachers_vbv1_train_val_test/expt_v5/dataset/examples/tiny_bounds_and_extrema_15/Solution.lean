import Mathlib

namespace Tiny

def solution (x y : Int) : Int := min (abs x) (abs y)

theorem spec_le_left (x y : Int) : solution x y ≤ abs x := by
  exact min_le_left (abs x) (abs y)

theorem test_first : solution (-2) 7 = 2 := by norm_num [solution]
theorem test_second : solution (-8) 3 = 3 := by norm_num [solution]

end Tiny

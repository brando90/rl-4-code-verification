import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := max x (min y z)

theorem spec_first_le (x y z : Int) : x ≤ solution x y z := by
  exact le_max_left x (min y z)

theorem test_first : solution 9 7 3 = 9 := by norm_num [solution]
theorem test_inner : solution 2 7 3 = 3 := by norm_num [solution]

end Tiny

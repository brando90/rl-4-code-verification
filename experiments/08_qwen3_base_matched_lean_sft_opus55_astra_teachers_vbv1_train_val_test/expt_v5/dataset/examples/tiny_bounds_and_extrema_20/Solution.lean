import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := max (min x y) (min x z)

theorem spec_left_le (x y z : Int) : min x y ≤ solution x y z := by
  exact le_max_left (min x y) (min x z)

theorem test_common : solution 2 7 3 = 2 := by norm_num [solution]
theorem test_first : solution 9 7 3 = 7 := by norm_num [solution]

end Tiny

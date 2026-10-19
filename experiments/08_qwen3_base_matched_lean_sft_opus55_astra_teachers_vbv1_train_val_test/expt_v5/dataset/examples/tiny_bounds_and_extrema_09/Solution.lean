import Mathlib

namespace Tiny

def solution (x y : Int) : Int := max x y - min x y

theorem spec_nonnegative (x y : Int) : 0 ≤ solution x y := by
  exact sub_nonneg.mpr min_le_max

theorem test_increasing : solution 2 7 = 5 := by norm_num [solution]
theorem test_decreasing : solution 7 2 = 5 := by norm_num [solution]

end Tiny

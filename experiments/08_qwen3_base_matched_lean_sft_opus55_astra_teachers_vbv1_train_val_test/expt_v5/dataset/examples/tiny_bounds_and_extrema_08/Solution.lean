import Mathlib

namespace Tiny

def solution (x : Int) (n : Nat) : Int := max (min x n) 0

theorem spec_nonnegative (x : Int) (n : Nat) : 0 ≤ solution x n := by
  exact le_max_right (min x n) 0

theorem test_negative : solution (-3) 5 = 0 := by norm_num [solution]
theorem test_above_bound : solution 9 5 = 5 := by norm_num [solution]

end Tiny

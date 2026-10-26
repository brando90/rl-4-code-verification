import Mathlib

namespace Tiny

def solution (x : Int) (n : Nat) : Int := min (max x 0) n

theorem spec_le_bound (x : Int) (n : Nat) : solution x n ≤ n := by
  exact min_le_right (max x 0) n

theorem test_negative : solution (-3) 5 = 0 := by norm_num [solution]
theorem test_above_bound : solution 9 5 = 5 := by norm_num [solution]

end Tiny
#print axioms Tiny.spec_le_bound
#print axioms Tiny.test_negative
#print axioms Tiny.test_above_bound

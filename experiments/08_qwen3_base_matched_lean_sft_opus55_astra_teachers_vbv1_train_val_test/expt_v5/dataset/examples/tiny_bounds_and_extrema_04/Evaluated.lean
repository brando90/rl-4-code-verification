import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := max (max x y) z

theorem spec_first_le (x y z : Int) : x ≤ solution x y z := by
  exact le_trans (le_max_left x y) (le_max_left (max x y) z)

theorem test_last_largest : solution 3 2 9 = 9 := by norm_num [solution]
theorem test_first_largest : solution 4 2 (-1) = 4 := by norm_num [solution]

end Tiny
#print axioms Tiny.spec_first_le
#print axioms Tiny.test_last_largest
#print axioms Tiny.test_first_largest

import Mathlib

namespace Tiny

def solution (x : Int) : Int := min x 0

theorem spec_nonpositive (x : Int) : solution x ≤ 0 := by
  exact min_le_right x 0

theorem test_negative : solution (-5) = -5 := by norm_num [solution]
theorem test_positive : solution 4 = 0 := by norm_num [solution]

end Tiny
#print axioms Tiny.spec_nonpositive
#print axioms Tiny.test_negative
#print axioms Tiny.test_positive

import Mathlib

namespace Tiny

def solution (x : Int) : Int := max x 0

theorem spec_nonnegative (x : Int) : 0 ≤ solution x := by
  exact le_max_right x 0

theorem test_negative : solution (-5) = 0 := by norm_num [solution]
theorem test_positive : solution 4 = 4 := by norm_num [solution]

end Tiny
#print axioms Tiny.spec_nonnegative
#print axioms Tiny.test_negative
#print axioms Tiny.test_positive

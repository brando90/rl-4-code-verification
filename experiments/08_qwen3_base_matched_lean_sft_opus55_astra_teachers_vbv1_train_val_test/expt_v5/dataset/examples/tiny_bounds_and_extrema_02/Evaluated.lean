import Mathlib

namespace Tiny

def solution (x y : Int) : Int := max x y

theorem spec_le_result (x y : Int) : x ≤ solution x y := by
  exact le_max_left x y

theorem test_negative : solution (-3) 2 = 2 := by norm_num [solution]
theorem test_order : solution 7 4 = 7 := by norm_num [solution]

end Tiny
#print axioms Tiny.spec_le_result
#print axioms Tiny.test_negative
#print axioms Tiny.test_order

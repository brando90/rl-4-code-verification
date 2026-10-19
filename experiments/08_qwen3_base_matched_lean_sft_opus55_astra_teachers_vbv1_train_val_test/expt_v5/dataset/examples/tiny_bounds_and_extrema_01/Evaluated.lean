import Mathlib

namespace Tiny

def solution (x y : Int) : Int := min x y

theorem spec_le_left (x y : Int) : solution x y ≤ x := by
  exact min_le_left x y

theorem test_negative : solution (-3) 2 = -3 := by norm_num [solution]
theorem test_order : solution 7 4 = 4 := by norm_num [solution]

end Tiny
#print axioms Tiny.spec_le_left
#print axioms Tiny.test_negative
#print axioms Tiny.test_order

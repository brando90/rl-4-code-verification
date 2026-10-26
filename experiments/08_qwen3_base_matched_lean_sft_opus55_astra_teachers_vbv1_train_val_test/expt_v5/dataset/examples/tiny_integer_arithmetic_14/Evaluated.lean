import Mathlib
namespace Tiny
def solution (x : Int) : Int := x ^ 3
theorem spec_negate (x : Int) : solution (-x) = -solution x := by
  simp only [solution]
  ring
theorem test_positive : solution 3 = 27 := by norm_num [solution]
theorem test_negative : solution (-2) = -8 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_negate
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative

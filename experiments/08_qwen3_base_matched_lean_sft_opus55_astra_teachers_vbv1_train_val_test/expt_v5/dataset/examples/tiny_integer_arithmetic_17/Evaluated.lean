import Mathlib
namespace Tiny
def solution (x y : Int) : Int := (-x) * (-y)
theorem spec_product (x y : Int) : solution x y = x * y := by
  simp only [solution]
  ring
theorem test_positive : solution 3 4 = 12 := by norm_num [solution]
theorem test_negative : solution (-2) 5 = -10 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_product
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative

import Mathlib
namespace Tiny
def solution (x y : Int) : Int × Int := (x + y, x - y)
theorem spec_sum (x y : Int) : (solution x y).1 + (solution x y).2 = 2 * x := by
  simp [solution]
  ring
theorem test_positive : solution 5 3 = (8, 2) := by norm_num [solution]
theorem test_negative : solution (-2) 4 = (2, -6) := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_sum
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative

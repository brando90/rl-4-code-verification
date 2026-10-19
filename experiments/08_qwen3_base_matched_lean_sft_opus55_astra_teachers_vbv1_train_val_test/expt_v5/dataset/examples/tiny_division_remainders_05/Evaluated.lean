import Mathlib
namespace Tiny
def solution (x : Int) : Int := x / 4
theorem spec_quadruple (x : Int) : solution (4 * x) = x := by simp [solution]
theorem test_negative : solution (-7) = -2 := by norm_num [solution]
theorem test_positive : solution 9 = 2 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_quadruple
#print axioms Tiny.test_negative
#print axioms Tiny.test_positive

import Mathlib
namespace Tiny
def solution (x : Int) : Int := x % 3
theorem spec_multiple (x : Int) : solution (3 * x) = 0 := by simp [solution]
theorem test_negative : solution (-7) = 2 := by norm_num [solution]
theorem test_positive : solution 8 = 2 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_multiple
#print axioms Tiny.test_negative
#print axioms Tiny.test_positive

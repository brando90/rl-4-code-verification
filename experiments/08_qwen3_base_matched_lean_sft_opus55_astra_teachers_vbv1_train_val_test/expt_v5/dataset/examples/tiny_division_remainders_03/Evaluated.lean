import Mathlib
namespace Tiny
def solution (x : Int) : Int := x / 3
theorem spec_triple (x : Int) : solution (3 * x) = x := by simp [solution]
theorem test_negative : solution (-7) = -3 := by norm_num [solution]
theorem test_positive : solution 8 = 2 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_triple
#print axioms Tiny.test_negative
#print axioms Tiny.test_positive

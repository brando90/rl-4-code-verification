import Mathlib
namespace Tiny
def solution (x : Int) : Int := (2 * x) / 2
theorem spec_identity (x : Int) : solution x = x := by simp [solution]
theorem test_negative : solution (-7) = -7 := by norm_num [solution]
theorem test_positive : solution 8 = 8 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_identity
#print axioms Tiny.test_negative
#print axioms Tiny.test_positive

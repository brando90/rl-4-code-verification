import Mathlib
namespace Tiny
def solution (pair : Int × Int) : Bool := pair.1 <= pair.2
theorem spec_reflexive (x : Int) : solution (x, x) = true := by simp [solution]
theorem test_true : solution (-2, 4) = true := by norm_num [solution]
theorem test_false : solution (5, 3) = false := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_reflexive
#print axioms Tiny.test_true
#print axioms Tiny.test_false

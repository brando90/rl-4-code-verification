import Mathlib
namespace Tiny
def solution (pair : Int × Int) : Bool := pair.1 == pair.2
theorem spec_equal (x : Int) : solution (x, x) = true := by simp [solution]
theorem test_equal : solution (2, 2) = true := by norm_num [solution]
theorem test_unequal : solution (-2, 4) = false := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_equal
#print axioms Tiny.test_equal
#print axioms Tiny.test_unequal

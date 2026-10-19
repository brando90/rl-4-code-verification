import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Bool := xs.length == ys.length
theorem spec_true_iff (xs ys : List Int) : solution xs ys = true ↔ xs.length = ys.length := by simp [solution]
theorem test_equal : solution [1, 2] [-3, 4] = true := by decide
theorem test_unequal : solution [1] [2, 3] = false := by decide
end Tiny
#print axioms Tiny.spec_true_iff
#print axioms Tiny.test_equal
#print axioms Tiny.test_unequal

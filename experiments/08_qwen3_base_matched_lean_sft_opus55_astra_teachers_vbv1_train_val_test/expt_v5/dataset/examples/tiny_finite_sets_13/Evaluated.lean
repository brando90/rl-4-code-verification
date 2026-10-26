import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Bool := decide (xs.toFinset = ys.toFinset)
theorem spec_true_iff (xs ys : List Int) : solution xs ys = true ↔ xs.toFinset = ys.toFinset := by
  simp [solution]
theorem test_equal : solution [1, 2, 1] [2, 1] = true := by decide
theorem test_different : solution [1] [2] = false := by decide
end Tiny
#print axioms Tiny.spec_true_iff
#print axioms Tiny.test_equal
#print axioms Tiny.test_different

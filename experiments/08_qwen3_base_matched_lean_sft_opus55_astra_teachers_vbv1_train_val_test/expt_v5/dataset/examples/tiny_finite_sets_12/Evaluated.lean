import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Bool := decide (Disjoint xs.toFinset ys.toFinset)
theorem spec_true_iff (xs ys : List Int) : solution xs ys = true ↔ ∀ x, x ∈ xs → x ∉ ys := by
  simp [solution, Finset.disjoint_left]
theorem test_disjoint : solution [1, 1] [2, 3] = true := by decide
theorem test_overlap : solution [1, 2] [2, 3] = false := by decide
end Tiny
#print axioms Tiny.spec_true_iff
#print axioms Tiny.test_disjoint
#print axioms Tiny.test_overlap

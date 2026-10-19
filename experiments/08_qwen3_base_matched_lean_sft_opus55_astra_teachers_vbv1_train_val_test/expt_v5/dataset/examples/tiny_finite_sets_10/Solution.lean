import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Bool := decide (xs.toFinset ⊆ ys.toFinset)
theorem spec_true_iff (xs ys : List Int) : solution xs ys = true ↔ xs.toFinset ⊆ ys.toFinset := by
  simp [solution]
theorem test_subset : solution [1, 1] [2, 1] = true := by decide
theorem test_not_subset : solution [1, 3] [1, 2] = false := by decide
end Tiny

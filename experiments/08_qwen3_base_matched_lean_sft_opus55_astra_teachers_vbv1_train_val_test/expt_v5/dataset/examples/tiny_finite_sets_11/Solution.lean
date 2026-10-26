import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Bool := decide (ys.toFinset ⊆ xs.toFinset)
theorem spec_true_iff (xs ys : List Int) : solution xs ys = true ↔ ys.toFinset ⊆ xs.toFinset := by
  simp [solution]
theorem test_superset : solution [1, 2] [1, 1] = true := by decide
theorem test_not_superset : solution [1] [1, 2] = false := by decide
end Tiny

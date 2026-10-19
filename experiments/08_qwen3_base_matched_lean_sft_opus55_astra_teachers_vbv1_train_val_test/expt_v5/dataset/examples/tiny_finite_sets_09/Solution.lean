import Mathlib
namespace Tiny
def solution (x : Int) (xs ys : List Int) : Bool := decide (x ∈ xs.toFinset \ ys.toFinset)
theorem spec_true_iff (x : Int) (xs ys : List Int) : solution x xs ys = true ↔ x ∈ xs ∧ x ∉ ys := by
  simp [solution]
theorem test_kept : solution 1 [1, 2] [2, 3] = true := by decide
theorem test_removed : solution 2 [1, 2] [2, 3] = false := by decide
end Tiny

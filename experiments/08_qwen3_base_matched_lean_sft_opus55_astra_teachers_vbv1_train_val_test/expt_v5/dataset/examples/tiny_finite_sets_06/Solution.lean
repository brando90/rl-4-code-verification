import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Bool := decide (x ∈ xs.toFinset)
theorem spec_true_iff (x : Int) (xs : List Int) : solution x xs = true ↔ x ∈ xs := by
  simp [solution]
theorem test_present : solution 2 [1, 2, 2] = true := by decide
theorem test_absent : solution 3 [1, 2] = false := by decide
end Tiny

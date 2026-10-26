import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Bool := decide (x ∈ xs.reverse)
theorem spec_membership (x : Int) (xs : List Int) : solution x xs = true ↔ x ∈ xs := by simp [solution]
theorem test_absent : solution 2 [1, 3] = false := by decide
theorem test_present : solution 2 [1, 2, 3] = true := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (x y : Int) (xs : List Int) : Bool := x == y || xs.contains x
theorem spec_membership (x y : Int) (xs : List Int) : solution x y xs = true ↔ x = y ∨ x ∈ xs := by simp [solution]
theorem test_head : solution 2 2 [3] = true := by decide
theorem test_absent : solution 4 2 [1, 3] = false := by decide
end Tiny

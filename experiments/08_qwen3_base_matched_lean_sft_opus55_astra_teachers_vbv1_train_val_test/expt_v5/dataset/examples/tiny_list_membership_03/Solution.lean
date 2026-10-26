import Mathlib
namespace Tiny
def solution (x : Int) (xs ys : List Int) : Bool := xs.contains x || ys.contains x
theorem spec_membership (x : Int) (xs ys : List Int) : solution x xs ys = true ↔ x ∈ xs ∨ x ∈ ys := by simp [solution]
theorem test_left : solution 2 [2] [3] = true := by decide
theorem test_absent : solution 4 [1] [2, 3] = false := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Bool := !xs.contains x
theorem spec_not_membership (x : Int) (xs : List Int) : solution x xs = true ↔ x ∉ xs := by simp [solution]
theorem test_present : solution 2 [1, 2, 3] = false := by decide
theorem test_absent : solution 4 [1, 2, 3] = true := by decide
end Tiny

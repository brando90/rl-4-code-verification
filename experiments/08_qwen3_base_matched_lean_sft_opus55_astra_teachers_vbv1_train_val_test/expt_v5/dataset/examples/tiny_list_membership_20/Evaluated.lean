import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Bool := xs.any fun a => 0 <= a && a == x
theorem spec_nonnegative_member (x : Int) (xs : List Int) : solution x xs = true ↔ ∃ a ∈ xs, 0 ≤ a ∧ a = x := by simp [solution]
theorem test_found : solution 2 [-2, 2, 3] = true := by decide
theorem test_filtered : solution (-2) [-2, 2, 3] = false := by decide
end Tiny
#print axioms Tiny.spec_nonnegative_member
#print axioms Tiny.test_found
#print axioms Tiny.test_filtered

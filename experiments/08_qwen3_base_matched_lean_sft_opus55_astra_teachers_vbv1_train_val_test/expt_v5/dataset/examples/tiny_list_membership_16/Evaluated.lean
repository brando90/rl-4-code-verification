import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Bool := xs.any fun a => a != x
theorem spec_different (x : Int) (xs : List Int) : solution x xs = true ↔ ∃ a ∈ xs, a ≠ x := by simp [solution]
theorem test_found : solution 2 [2, 3] = true := by decide
theorem test_absent : solution 2 [2, 2] = false := by decide
end Tiny
#print axioms Tiny.spec_different
#print axioms Tiny.test_found
#print axioms Tiny.test_absent

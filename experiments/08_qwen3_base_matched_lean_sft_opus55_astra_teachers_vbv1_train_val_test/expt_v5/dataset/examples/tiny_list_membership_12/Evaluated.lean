import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Bool := xs.contains x
theorem spec_any_equal (x : Int) (xs : List Int) : solution x xs = true ↔ ∃ a ∈ xs, a = x := by simp [solution]
theorem test_found : solution 2 [1, 2, 3] = true := by decide
theorem test_absent : solution 4 [1, 2, 3] = false := by decide
end Tiny
#print axioms Tiny.spec_any_equal
#print axioms Tiny.test_found
#print axioms Tiny.test_absent

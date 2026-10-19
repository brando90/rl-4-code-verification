import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Bool := xs.all fun a => a == x
theorem spec_all_equal (x : Int) (xs : List Int) : solution x xs = true ↔ ∀ a ∈ xs, a = x := by simp [solution]
theorem test_all_equal : solution 2 [2, 2, 2] = true := by decide
theorem test_not_all_equal : solution 2 [2, 3] = false := by decide
end Tiny
#print axioms Tiny.spec_all_equal
#print axioms Tiny.test_all_equal
#print axioms Tiny.test_not_all_equal

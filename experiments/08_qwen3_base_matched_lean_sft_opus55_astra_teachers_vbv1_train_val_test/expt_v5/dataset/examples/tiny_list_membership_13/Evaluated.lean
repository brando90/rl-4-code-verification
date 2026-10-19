import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Bool := xs.all fun a => ys.contains a
theorem spec_subset (xs ys : List Int) : solution xs ys = true ↔ ∀ a ∈ xs, a ∈ ys := by simp [solution]
theorem test_subset : solution [1, 2] [2, 1, 3] = true := by decide
theorem test_not_subset : solution [1, 4] [1, 2, 3] = false := by decide
end Tiny
#print axioms Tiny.spec_subset
#print axioms Tiny.test_subset
#print axioms Tiny.test_not_subset

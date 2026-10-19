import Mathlib
namespace Tiny
def solution (xs : List Int) : Bool := xs.all fun a => 0 <= a
theorem spec_nonnegative (xs : List Int) : solution xs = true ↔ ∀ a ∈ xs, 0 ≤ a := by simp [solution]
theorem test_all_nonnegative : solution [0, 2, 5] = true := by decide
theorem test_negative : solution [0, -2, 5] = false := by decide
end Tiny

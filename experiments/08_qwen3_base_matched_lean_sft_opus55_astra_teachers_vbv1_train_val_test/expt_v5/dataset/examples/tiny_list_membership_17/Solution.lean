import Mathlib
namespace Tiny
def solution (xs : List Int) : Bool := xs.all fun a => a % 2 == 0
theorem spec_even (xs : List Int) : solution xs = true ↔ ∀ a ∈ xs, a % 2 = 0 := by simp [solution]
theorem test_all_even : solution [-2, 0, 4] = true := by decide
theorem test_odd : solution [2, 3, 4] = false := by decide
end Tiny

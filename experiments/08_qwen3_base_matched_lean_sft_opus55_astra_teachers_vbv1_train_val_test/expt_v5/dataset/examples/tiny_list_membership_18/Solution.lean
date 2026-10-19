import Mathlib
namespace Tiny
def solution (xs : List Int) : Bool := xs.any fun a => a % 2 == 0
theorem spec_even (xs : List Int) : solution xs = true ↔ ∃ a ∈ xs, a % 2 = 0 := by simp [solution]
theorem test_found : solution [-3, 2, 5] = true := by decide
theorem test_absent : solution [-3, 1, 5] = false := by decide
end Tiny

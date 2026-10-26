import Mathlib
namespace Tiny
def solution (xs : List Int) : Bool := xs.any fun a => a < 0
theorem spec_negative (xs : List Int) : solution xs = true ↔ ∃ a ∈ xs, a < 0 := by simp [solution]
theorem test_found : solution [0, -2, 5] = true := by decide
theorem test_absent : solution [0, 2, 5] = false := by decide
end Tiny

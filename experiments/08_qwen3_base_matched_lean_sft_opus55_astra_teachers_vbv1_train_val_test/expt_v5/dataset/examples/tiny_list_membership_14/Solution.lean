import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Bool := xs.any fun a => ys.contains a
theorem spec_overlap (xs ys : List Int) : solution xs ys = true ↔ ∃ a ∈ xs, a ∈ ys := by simp [solution]
theorem test_overlap : solution [1, 4] [2, 4] = true := by decide
theorem test_disjoint : solution [1, 4] [2, 3] = false := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (xs : List Int) : Nat := xs.toFinset.card
theorem spec_zero_iff (xs : List Int) : solution xs = 0 ↔ xs = [] := by
  simp [solution]
theorem test_duplicates : solution [1, 1, 2] = 2 := by decide
theorem test_empty : solution [] = 0 := by decide
end Tiny

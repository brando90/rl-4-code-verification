import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Nat := (xs.toFinset \ ys.toFinset).card
theorem spec_empty_right (xs : List Int) : solution xs [] = xs.toFinset.card := by
  simp [solution]
theorem test_remove : solution [1, 2, 2, 3] [2] = 2 := by decide
theorem test_empty : solution [] [1] = 0 := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs.take 1
theorem spec_shape (xs : List Int) : solution xs = [] ∨ ∃ x, solution xs = [x] := by
  cases xs with
  | nil => simp [solution]
  | cons x xs => simp [solution]
theorem test_empty : solution [] = [] := by decide
theorem test_head : solution [2, 3] = [2] := by decide
end Tiny

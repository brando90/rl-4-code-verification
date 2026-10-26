import Mathlib
namespace Tiny
def solution : List Int → List Int
  | [] => []
  | [x] => [x]
  | _ :: xs => solution xs
theorem spec_shape (xs : List Int) : solution xs = [] ∨ ∃ x, solution xs = [x] := by
  induction xs with
  | nil => left; rfl
  | cons a xs ih =>
    cases xs with
    | nil => right; exact ⟨a, rfl⟩
    | cons b xs => simpa [solution] using ih
theorem test_empty : solution [] = [] := by decide
theorem test_last : solution [2, 3] = [3] := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := xs.filter fun a => decide (a ∈ ys)
theorem spec_members (a : Int) (xs ys : List Int) : a ∈ solution xs ys ↔ a ∈ xs ∧ a ∈ ys := by simp [solution]
theorem test_duplicates : solution [1, 2, 1, 3] [1, 3] = [1, 1, 3] := by decide
theorem test_empty_right : solution [1, 2] [] = [] := by decide
end Tiny

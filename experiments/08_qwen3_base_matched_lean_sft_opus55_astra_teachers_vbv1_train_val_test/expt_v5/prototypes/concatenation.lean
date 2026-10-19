import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := xs ++ ys
theorem spec_length (xs ys : List Int) : (solution xs ys).length = xs.length + ys.length := by
  simp [solution]
theorem spec_membership (x : Int) (xs ys : List Int) : x ∈ solution xs ys ↔ x ∈ xs ∨ x ∈ ys := by
  simp [solution]
theorem test_empty : solution [] [1] = [1] := by decide
theorem test_order : solution [2, 1] [2] = [2, 1, 2] := by decide
end Tiny

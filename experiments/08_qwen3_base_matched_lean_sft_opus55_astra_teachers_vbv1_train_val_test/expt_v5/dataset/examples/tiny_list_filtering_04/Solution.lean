import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs.filter fun a => decide (a <= 0)
theorem spec_members (a : Int) (xs : List Int) : a ∈ solution xs ↔ a ∈ xs ∧ a <= 0 := by simp [solution]
theorem test_mixed : solution [-2, 0, 3, -1] = [-2, 0, -1] := by decide
theorem test_empty : solution [] = [] := by decide
end Tiny

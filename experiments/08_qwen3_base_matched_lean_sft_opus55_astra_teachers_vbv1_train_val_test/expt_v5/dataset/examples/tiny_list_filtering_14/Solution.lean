import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs.filter fun a => decide (a % 2 != 0)
theorem spec_members (a : Int) (xs : List Int) : a ∈ solution xs ↔ a ∈ xs ∧ a % 2 != 0 := by simp [solution]
theorem test_mixed : solution [-3, -2, 0, 1, 4] = [-3, 1] := by decide
theorem test_empty : solution [] = [] := by decide
end Tiny

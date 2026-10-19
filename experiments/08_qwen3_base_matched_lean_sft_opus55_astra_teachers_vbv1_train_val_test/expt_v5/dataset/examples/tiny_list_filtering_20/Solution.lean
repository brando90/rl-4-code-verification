import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := (xs.filter fun a => decide (a >= 0)).map fun a => a + 1
theorem spec_positive (a : Int) (xs : List Int) : a ∈ solution xs → a > 0 := by
  simp [solution]
  omega
theorem test_mixed : solution [-2, 0, 3] = [1, 4] := by decide
theorem test_empty : solution [] = [] := by decide
end Tiny

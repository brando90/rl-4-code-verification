import Mathlib
namespace Tiny
def solution (xs : List Int) : Nat := (xs.filter fun a => decide (a > 0)).length
theorem spec_cons (a : Int) (xs : List Int) :
    solution (a :: xs) = if decide (a > 0) then solution xs + 1 else solution xs := by
  by_cases h : 0 < a <;> simp [solution, h]
theorem test_mixed : solution [-2, 0, 3, 4] = 2 := by decide
theorem test_empty : solution [] = 0 := by decide
end Tiny

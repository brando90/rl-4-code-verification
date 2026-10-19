import Mathlib
namespace Tiny
def solution (xs : List Int) : Nat := (xs.filter fun a => a % 2 != 0).length
theorem spec_cons (a : Int) (xs : List Int) :
    solution (a :: xs) = if a % 2 != 0 then solution xs + 1 else solution xs := by
  by_cases h : a % 2 = 1 <;> simp [solution, h]
theorem test_mixed : solution [-2, -1, 0, 3, 4] = 2 := by decide
theorem test_empty : solution [] = 0 := by decide
end Tiny

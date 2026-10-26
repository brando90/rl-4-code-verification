import Mathlib
namespace Tiny
def solution (xs : List Int) : Int := (xs.filter fun a => a < 0).sum
theorem spec_cons_negative (a : Int) (xs : List Int) (h : a < 0) : solution (a :: xs) = a + solution xs := by simp [solution, h]
theorem test_empty : solution [] = 0 := by decide
theorem test_mixed : solution [3, -5, 0, 2] = -5 := by decide
end Tiny

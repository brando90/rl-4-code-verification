import Mathlib
namespace Tiny
def solution (xs : List Int) : Nat := (xs.filter fun a => a > 0).length
theorem spec_positive_head (a : Int) (xs : List Int) (h : 0 < a) : solution (a :: xs) = solution xs + 1 := by simp [solution, h]
theorem test_none : solution [-3, 0] = 0 := by decide
theorem test_some : solution [-1, 2, 3] = 2 := by decide
end Tiny

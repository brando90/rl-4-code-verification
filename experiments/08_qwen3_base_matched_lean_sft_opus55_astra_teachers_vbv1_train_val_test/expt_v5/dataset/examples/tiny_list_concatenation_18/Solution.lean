import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Bool := (xs ++ ys).all fun a => decide (a >= 0)
theorem spec_empty_right (xs : List Int) : solution xs [] = xs.all (fun a => decide (a >= 0)) := by simp [solution]
theorem test_nonnegative : solution [0, 2] [3] = true := by decide
theorem test_negative : solution [0, -1] [3] = false := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := (xs ++ ys).filter fun a => decide (a > 0)
theorem spec_filter (xs ys : List Int) : solution xs ys = xs.filter (fun a => decide (a > 0)) ++ ys.filter (fun a => decide (a > 0)) := by simp [solution]
theorem test_empty : solution [] [0, 2, -1] = [2] := by decide
theorem test_values : solution [2, -1] [3, 0] = [2, 3] := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := (xs ++ ys).reverse
theorem spec_reverse (xs ys : List Int) : solution xs ys = ys.reverse ++ xs.reverse := by simp [solution]
theorem test_empty : solution [] [1, 2] = [2, 1] := by decide
theorem test_order : solution [2, -1] [3] = [3, -1, 2] := by decide
end Tiny

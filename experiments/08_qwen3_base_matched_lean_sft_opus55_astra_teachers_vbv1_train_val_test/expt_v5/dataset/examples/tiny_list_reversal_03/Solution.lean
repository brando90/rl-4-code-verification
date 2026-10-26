import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := (xs ++ ys).reverse
theorem spec_append (xs ys : List Int) : solution xs ys = ys.reverse ++ xs.reverse := by simp [solution]
theorem test_empty : solution [] [1] = [1] := by decide
theorem test_order : solution [1, 2] [3, 4] = [4, 3, 2, 1] := by decide
end Tiny

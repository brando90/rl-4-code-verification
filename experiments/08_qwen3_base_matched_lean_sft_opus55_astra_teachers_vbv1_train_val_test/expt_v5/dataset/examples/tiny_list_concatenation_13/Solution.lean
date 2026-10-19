import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := xs ++ ys.reverse
theorem spec_length (xs ys : List Int) : (solution xs ys).length = xs.length + ys.length := by simp [solution]
theorem test_empty : solution [1, 2] [] = [1, 2] := by decide
theorem test_order : solution [2] [-1, 3] = [2, 3, -1] := by decide
end Tiny

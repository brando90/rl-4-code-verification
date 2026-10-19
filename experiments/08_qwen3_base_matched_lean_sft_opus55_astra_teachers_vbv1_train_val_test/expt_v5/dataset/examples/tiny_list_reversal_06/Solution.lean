import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := xs.reverse ++ ys.reverse
theorem spec_length (xs ys : List Int) : (solution xs ys).length = xs.length + ys.length := by simp [solution]
theorem test_empty : solution [] [1] = [1] := by decide
theorem test_order : solution [1, 2] [3, 4] = [2, 1, 4, 3] := by decide
end Tiny

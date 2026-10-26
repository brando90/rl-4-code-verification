import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := [xs.sum]
theorem spec_head (xs : List Int) : (solution xs).head? = some xs.sum := by simp [solution]
theorem test_empty : solution [] = [0] := by decide
theorem test_sum : solution [2, -1, 4] = [5] := by decide
end Tiny

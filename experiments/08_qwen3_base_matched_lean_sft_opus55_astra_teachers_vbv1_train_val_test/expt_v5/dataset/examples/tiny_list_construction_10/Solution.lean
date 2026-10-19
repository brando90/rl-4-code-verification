import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs ++ xs ++ xs
theorem spec_length (xs : List Int) : (solution xs).length = xs.length + (xs.length + xs.length) := by simp [solution]
theorem test_empty : solution [] = [] := by decide
theorem test_repeat : solution [1, -2] = [1, -2, 1, -2, 1, -2] := by decide
end Tiny

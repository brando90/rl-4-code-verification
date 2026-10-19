import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs ++ []
theorem spec_identity (xs : List Int) : solution xs = xs := by simp [solution]
theorem test_empty : solution [] = [] := by decide
theorem test_values : solution [2, -1] = [2, -1] := by decide
end Tiny

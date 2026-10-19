import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs
theorem spec_identity (xs : List Int) : solution xs = xs := by rfl
theorem test_values : solution [1, -2, 1] = [1, -2, 1] := by decide
theorem test_empty : solution [] = [] := by decide
end Tiny

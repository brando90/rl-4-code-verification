import Mathlib
namespace Tiny
def solution (xs : List Int) : Int := xs.sum
theorem spec_cons (x : Int) (xs : List Int) : solution (x :: xs) = x + solution xs := by rfl
theorem test_empty : solution [] = 0 := by decide
theorem test_mixed : solution [3, -5, 2] = 0 := by decide
end Tiny

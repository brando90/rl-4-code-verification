import Mathlib
namespace Tiny
def solution (xs : List Int) : Int := (xs.map fun a => a * a).sum
theorem spec_cons (a : Int) (xs : List Int) : solution (a :: xs) = a * a + solution xs := by rfl
theorem test_empty : solution [] = 0 := by decide
theorem test_mixed : solution [3, -5, 2] = 38 := by decide
end Tiny

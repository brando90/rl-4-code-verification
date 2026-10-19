import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs.drop 1
theorem spec_cons (x : Int) (xs : List Int) : solution (x :: xs) = xs := by rfl
theorem test_empty : solution [] = [] := by decide
theorem test_tail : solution [2, 3] = [3] := by decide
end Tiny

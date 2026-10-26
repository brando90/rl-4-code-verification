import Mathlib
namespace Tiny
def solution (xs : List Int) : Option Int := xs.head?
theorem spec_cons (x : Int) (xs : List Int) : solution (x :: xs) = some x := by rfl
theorem test_empty : solution [] = none := by decide
theorem test_values : solution [2, -1] = some 2 := by decide
end Tiny

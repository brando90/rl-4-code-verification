import Mathlib
namespace Tiny
def solution (xs : List Int) : Bool := xs.sum % 2 == 0
theorem spec_cons (x : Int) (xs : List Int) : solution (x :: xs) = ((x + xs.sum) % 2 == 0) := by rfl
theorem test_empty : solution [] = true := by decide
theorem test_odd_sum : solution [1, -2, 4] = false := by decide
end Tiny

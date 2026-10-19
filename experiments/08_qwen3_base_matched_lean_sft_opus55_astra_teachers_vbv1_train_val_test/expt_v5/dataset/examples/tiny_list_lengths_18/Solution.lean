import Mathlib
namespace Tiny
def solution (xs : List Int) : Nat := xs.tail.length
theorem spec_cons (x : Int) (xs : List Int) : solution (x :: xs) = xs.length := by rfl
theorem test_empty : solution [] = 0 := by decide
theorem test_many : solution [1, 2, 3] = 2 := by decide
end Tiny

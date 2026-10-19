import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : Bool := xs.take n == xs
theorem spec_zero (xs : List Int) : solution 0 xs = (xs == []) := by
  cases xs <;> rfl
theorem test_enough : solution 3 [1, 2] = true := by decide
theorem test_short : solution 1 [1, 2] = false := by decide
end Tiny

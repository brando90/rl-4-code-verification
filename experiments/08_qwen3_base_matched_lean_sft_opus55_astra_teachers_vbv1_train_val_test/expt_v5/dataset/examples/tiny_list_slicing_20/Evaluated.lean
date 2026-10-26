import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : Bool := xs.drop n == []
theorem spec_zero (xs : List Int) : solution 0 xs = (xs == []) := by rfl
theorem test_enough : solution 3 [1, 2] = true := by decide
theorem test_short : solution 1 [1, 2] = false := by decide
end Tiny
#print axioms Tiny.spec_zero
#print axioms Tiny.test_enough
#print axioms Tiny.test_short

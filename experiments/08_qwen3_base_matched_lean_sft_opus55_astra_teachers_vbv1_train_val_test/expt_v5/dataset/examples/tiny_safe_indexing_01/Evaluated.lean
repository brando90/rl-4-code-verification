import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs : List Int) : Int := xs.getD n x
theorem spec_zero (x a : Int) (xs : List Int) : solution x 0 (a :: xs) = a := by rfl
theorem test_index : solution 9 1 [2, 3] = 3 := by decide
theorem test_default : solution 9 2 [2] = 9 := by decide
end Tiny
#print axioms Tiny.spec_zero
#print axioms Tiny.test_index
#print axioms Tiny.test_default

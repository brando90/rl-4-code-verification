import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Int := xs.getD 1 x
theorem spec_pair (x a b : Int) (xs : List Int) : solution x (a :: b :: xs) = b := by rfl
theorem test_second : solution 9 [2, 3] = 3 := by decide
theorem test_default : solution 9 [2] = 9 := by decide
end Tiny
#print axioms Tiny.spec_pair
#print axioms Tiny.test_second
#print axioms Tiny.test_default

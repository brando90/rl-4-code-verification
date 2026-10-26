import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Int := xs.headD x
theorem spec_empty (x : Int) : solution x [] = x := by rfl
theorem spec_cons (x a : Int) (xs : List Int) : solution x (a :: xs) = a := by rfl
theorem test_default : solution 9 [] = 9 := by decide
theorem test_first : solution 9 [1, -2, 3] = 1 := by decide
end Tiny
#print axioms Tiny.spec_empty
#print axioms Tiny.spec_cons
#print axioms Tiny.test_default
#print axioms Tiny.test_first

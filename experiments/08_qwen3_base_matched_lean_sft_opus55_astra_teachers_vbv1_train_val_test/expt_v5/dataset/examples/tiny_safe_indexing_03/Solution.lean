import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Int := xs.getLastD x
theorem spec_singleton (x a : Int) : solution x [a] = a := by rfl
theorem test_last : solution 9 [2, 3] = 3 := by decide
theorem test_default : solution 9 [] = 9 := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Int := xs.headD x
theorem spec_empty (x : Int) : solution x [] = x := by
  rfl
theorem spec_cons (x a : Int) (xs : List Int) : solution x (a :: xs) = a := by
  rfl
theorem test_nonempty : solution 9 [2, 3] = 2 := by decide
theorem test_default : solution 9 [] = 9 := by decide
end Tiny

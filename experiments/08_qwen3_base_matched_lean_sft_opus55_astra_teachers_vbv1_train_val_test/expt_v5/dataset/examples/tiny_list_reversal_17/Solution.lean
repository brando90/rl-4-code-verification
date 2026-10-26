import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Int := xs.reverse.headD x
theorem spec_empty (x : Int) : solution x [] = x := by rfl
theorem spec_append (x a : Int) (xs : List Int) : solution x (xs ++ [a]) = a := by simp [solution]
theorem test_default : solution 9 [] = 9 := by decide
theorem test_last : solution 9 [1, -2, 3] = 3 := by decide
end Tiny

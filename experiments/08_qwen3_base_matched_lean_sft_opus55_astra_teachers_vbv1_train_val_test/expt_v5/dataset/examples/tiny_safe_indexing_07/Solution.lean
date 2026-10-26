import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Int := ([x] ++ xs).getLastD x
theorem spec_empty (x : Int) : solution x [] = x := by rfl
theorem test_last : solution 9 [2, 3] = 3 := by decide
theorem test_default : solution 9 [] = 9 := by decide
end Tiny

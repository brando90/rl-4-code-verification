import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Int := (xs ++ [x]).getLastD x
theorem spec_value (x : Int) (xs : List Int) : solution x xs = x := by simp [solution]
theorem test_nonempty : solution 9 [2, 3] = 9 := by decide
theorem test_empty : solution 9 [] = 9 := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (x y : Int) (xs : List Int) : Nat := xs.count x
theorem spec_append (x y : Int) (xs zs : List Int) :
    solution x y (xs ++ zs) = solution x y xs + solution x y zs := by simp [solution]
theorem test_shifted : solution 2 (-3) [2, 1, 2] = 2 := by decide
theorem test_empty : solution 2 5 [] = 0 := by decide
end Tiny

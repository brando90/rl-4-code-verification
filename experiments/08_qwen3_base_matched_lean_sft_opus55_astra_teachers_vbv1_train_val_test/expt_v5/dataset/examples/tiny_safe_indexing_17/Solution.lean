import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs ys : List Int) : Int := (xs ++ ys).getD n x
theorem spec_empty (x : Int) (n : Nat) : solution x n [] [] = x := by rfl
theorem test_left : solution 9 1 [2, 3] [4] = 3 := by decide
theorem test_right : solution 9 2 [2] [3, 4] = 4 := by decide
end Tiny

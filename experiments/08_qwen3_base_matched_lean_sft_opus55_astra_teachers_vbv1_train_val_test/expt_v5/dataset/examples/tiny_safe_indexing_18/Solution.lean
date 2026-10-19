import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs : List Int) : Int := xs.reverse.getD n x
theorem spec_empty (x : Int) (n : Nat) : solution x n [] = x := by rfl
theorem test_reversed : solution 9 1 [2, 3, 4] = 3 := by decide
theorem test_default : solution 9 2 [2] = 9 := by decide
end Tiny

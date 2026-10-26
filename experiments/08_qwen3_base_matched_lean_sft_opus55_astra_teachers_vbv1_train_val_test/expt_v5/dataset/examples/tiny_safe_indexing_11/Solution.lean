import Mathlib
namespace Tiny
def solution (y : Int) (n : Nat) (xs : List Int) : Int := xs.getD n 0 + y
theorem spec_empty (y : Int) (n : Nat) : solution y n [] = y := by simp [solution]
theorem test_index : solution 5 1 [2, 3] = 8 := by decide
theorem test_default : solution 5 2 [2] = 5 := by decide
end Tiny

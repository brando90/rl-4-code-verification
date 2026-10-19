import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) : Int := (n : Int) * x
theorem spec_zero (x : Int) : solution x 0 = 0 := by simp [solution]
theorem test_zero : solution 4 0 = 0 := by decide
theorem test_repeat : solution (-2) 3 = -6 := by decide
end Tiny

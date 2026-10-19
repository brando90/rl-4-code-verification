import Mathlib
namespace Tiny
def solution (x y : Int) : Bool := x % 2 != y % 2
theorem spec_self (x : Int) : solution x x = false := by simp [solution]
theorem test_different_parity : solution (-3) 2 = true := by decide
theorem test_same_parity : solution 2 4 = false := by decide
end Tiny

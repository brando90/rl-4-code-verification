import Mathlib
namespace Tiny
def solution (x y : Int) : Bool := x % 2 == y % 2
theorem spec_self (x : Int) : solution x x = true := by simp [solution]
theorem test_same_parity : solution (-3) 5 = true := by decide
theorem test_different_parity : solution 2 5 = false := by decide
end Tiny

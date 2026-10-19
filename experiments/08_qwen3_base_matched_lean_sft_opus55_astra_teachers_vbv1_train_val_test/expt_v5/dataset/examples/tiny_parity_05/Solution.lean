import Mathlib
namespace Tiny
def solution (x y : Int) : Bool := (x - y) % 2 == 0
theorem spec_self (x : Int) : solution x x = true := by simp [solution]
theorem test_even_difference : solution 7 3 = true := by decide
theorem test_odd_difference : solution (-2) 1 = false := by decide
end Tiny

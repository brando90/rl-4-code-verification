import Mathlib
namespace Tiny
def solution (x : Int) : Int := (x + 1) % 2
theorem spec_add_zero (x : Int) : solution (x + 0) = solution x := by simp [solution]
theorem test_even_input : solution 4 = 1 := by decide
theorem test_negative_odd_input : solution (-3) = 0 := by decide
end Tiny

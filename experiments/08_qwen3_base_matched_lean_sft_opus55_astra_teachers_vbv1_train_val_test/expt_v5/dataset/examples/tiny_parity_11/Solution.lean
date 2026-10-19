import Mathlib
namespace Tiny
def solution (x : Int) : Bool := (2 * x) % 2 == 0
theorem spec_always_even (x : Int) : solution x = true := by
  simp [solution, Int.mul_emod]
theorem test_positive : solution 7 = true := by decide
theorem test_negative : solution (-4) = true := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (x : Int) : Bool := (2 * x + 1) % 2 != 0
theorem spec_always_odd (x : Int) : solution x = true := by
  simp [solution, Int.add_emod, Int.mul_emod]
theorem test_positive : solution 7 = true := by decide
theorem test_negative : solution (-4) = true := by decide
end Tiny

import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := x * y + x * z

theorem spec_factor (x y z : Int) : solution x y z = x * (y + z) := by
  simp [solution]
  ring

theorem test_positive : solution 2 3 4 = 14 := by decide
theorem test_negative : solution (-2) 3 (-5) = 4 := by decide

end Tiny
#print axioms Tiny.spec_factor
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative

import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := x * (y - z) + x * z

theorem spec_cancel (x y z : Int) : solution x y z = x * y := by
  simp [solution]
  ring

theorem test_positive : solution 2 3 4 = 6 := by decide
theorem test_negative : solution (-2) 3 (-5) = -6 := by decide

end Tiny

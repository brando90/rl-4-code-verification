import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := x * y + y * z + z * x

theorem spec_symmetric (x y z : Int) : solution x y z = solution y x z := by
  simp [solution]
  ring

theorem test_positive : solution 1 2 3 = 11 := by decide
theorem test_negative : solution (-2) 5 1 = -7 := by decide

end Tiny

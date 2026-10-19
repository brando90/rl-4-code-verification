import Mathlib

namespace Tiny

def solution (x y : Int) : Int := (x - y) * (x - y)

theorem spec_square (x y : Int) : solution x y = (x - y) ^ 2 := by
  simp [solution]
  ring

theorem test_positive : solution 5 2 = 9 := by decide
theorem test_negative : solution (-4) 1 = 25 := by decide

end Tiny

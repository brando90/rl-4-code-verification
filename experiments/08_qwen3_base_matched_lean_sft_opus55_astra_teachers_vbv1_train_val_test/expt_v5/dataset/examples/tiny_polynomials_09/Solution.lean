import Mathlib

namespace Tiny

def solution (x : Int) : Int := (x + 1) ^ 2

theorem spec_expand (x : Int) : solution x = x ^ 2 + 2 * x + 1 := by
  simp [solution]
  ring

theorem test_positive : solution 3 = 16 := by decide
theorem test_negative : solution (-5) = 16 := by decide

end Tiny

import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := (x + y + z) ^ 2

theorem spec_expand (x y z : Int) :
    solution x y z = x ^ 2 + y ^ 2 + z ^ 2 + 2 * x * y + 2 * x * z + 2 * y * z := by
  simp [solution]
  ring

theorem test_positive : solution 1 2 3 = 36 := by decide
theorem test_negative : solution (-2) 5 1 = 16 := by decide

end Tiny

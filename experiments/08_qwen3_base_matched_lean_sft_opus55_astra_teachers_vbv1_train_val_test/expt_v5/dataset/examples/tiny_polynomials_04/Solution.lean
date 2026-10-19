import Mathlib

namespace Tiny

def solution (x y : Int) : Int := x * x - y * y

theorem spec_factorization (x y : Int) : solution x y = (x + y) * (x - y) := by
  simp [solution]
  ring

theorem test_positive : solution 5 2 = 21 := by decide
theorem test_negative : solution (-3) 4 = -7 := by decide

end Tiny

import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := x * (y * z)

theorem spec_associative (x y z : Int) : solution x y z = x * y * z := by
  simp [solution, mul_assoc]

theorem test_positive : solution 2 3 4 = 24 := by decide
theorem test_negative : solution (-2) 3 (-4) = 24 := by decide

end Tiny
#print axioms Tiny.spec_associative
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative

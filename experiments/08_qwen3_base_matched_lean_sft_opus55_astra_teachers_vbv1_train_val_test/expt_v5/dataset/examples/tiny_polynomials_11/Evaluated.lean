import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := (x + y) * (y + z)

theorem spec_expand (x y z : Int) : solution x y z = x * y + x * z + y ^ 2 + y * z := by
  simp [solution]
  ring

theorem test_positive : solution 1 2 3 = 15 := by decide
theorem test_negative : solution (-2) 5 1 = 18 := by decide

end Tiny
#print axioms Tiny.spec_expand
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative

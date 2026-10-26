import Mathlib
namespace Tiny
def solution (x y z : Nat) : Nat := x * (y + z)
theorem spec_distribute (x y z : Nat) : solution x y z = x * y + x * z := by
  simp [solution, Nat.mul_add]
theorem test_small : solution 2 3 4 = 14 := by norm_num [solution]
theorem test_zero : solution 0 3 4 = 0 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_distribute
#print axioms Tiny.test_small
#print axioms Tiny.test_zero

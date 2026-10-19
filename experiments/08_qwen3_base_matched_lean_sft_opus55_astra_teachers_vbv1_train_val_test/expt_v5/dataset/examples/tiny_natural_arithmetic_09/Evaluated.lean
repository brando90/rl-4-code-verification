import Mathlib
namespace Tiny
def solution (x y z : Nat) : Nat := x + y * z
theorem spec_reorder (x y z : Nat) : solution x y z = z * y + x := by
  simp [solution, Nat.add_comm, Nat.mul_comm]
theorem test_small : solution 2 3 4 = 14 := by norm_num [solution]
theorem test_zero : solution 2 0 4 = 2 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_reorder
#print axioms Tiny.test_small
#print axioms Tiny.test_zero

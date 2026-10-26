import Mathlib
namespace Tiny
def solution (x y : Nat) : Nat := x + 2 * y
theorem spec_reorder (x y : Nat) : solution x y = 2 * y + x := by
  simp [solution, Nat.add_comm]
theorem test_small : solution 3 4 = 11 := by norm_num [solution]
theorem test_zero : solution 7 0 = 7 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_reorder
#print axioms Tiny.test_small
#print axioms Tiny.test_zero

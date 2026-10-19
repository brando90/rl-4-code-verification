import Mathlib
namespace Tiny
def solution (x y z : Nat) : Nat := x + y + z
theorem spec_swap (x y z : Nat) : solution x y z = solution y x z := by
  simp [solution, Nat.add_comm]
theorem test_small : solution 2 3 4 = 9 := by norm_num [solution]
theorem test_zero : solution 0 0 7 = 7 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_swap
#print axioms Tiny.test_small
#print axioms Tiny.test_zero

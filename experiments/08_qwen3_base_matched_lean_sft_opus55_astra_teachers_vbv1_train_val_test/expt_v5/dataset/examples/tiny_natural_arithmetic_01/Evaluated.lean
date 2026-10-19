import Mathlib
namespace Tiny
def solution (x y : Nat) : Nat := x + y
theorem spec_commutative (x y : Nat) : solution x y = solution y x := by
  simp [solution, Nat.add_comm]
theorem test_small : solution 2 3 = 5 := by norm_num [solution]
theorem test_zero : solution 0 7 = 7 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_commutative
#print axioms Tiny.test_small
#print axioms Tiny.test_zero

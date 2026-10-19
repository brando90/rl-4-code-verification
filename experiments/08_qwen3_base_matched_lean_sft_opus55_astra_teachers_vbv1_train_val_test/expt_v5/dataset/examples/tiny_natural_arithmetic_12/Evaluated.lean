import Mathlib
namespace Tiny
def solution (x y : Nat) : Nat := x * x + y * y
theorem spec_symmetric (x y : Nat) : solution x y = solution y x := by
  simp [solution, Nat.add_comm]
theorem test_small : solution 3 4 = 25 := by norm_num [solution]
theorem test_zero : solution 0 5 = 25 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_symmetric
#print axioms Tiny.test_small
#print axioms Tiny.test_zero

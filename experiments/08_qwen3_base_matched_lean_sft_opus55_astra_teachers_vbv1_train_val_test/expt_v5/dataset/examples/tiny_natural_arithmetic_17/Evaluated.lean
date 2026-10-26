import Mathlib
namespace Tiny
def solution (x y z : Nat) : Nat := min (x + y) z
theorem spec_left_iff (x y z : Nat) : solution x y z = x + y ↔ x + y ≤ z := by
  simp [solution]
theorem test_sum : solution 2 3 9 = 5 := by norm_num [solution]
theorem test_cap : solution 5 6 7 = 7 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_left_iff
#print axioms Tiny.test_sum
#print axioms Tiny.test_cap

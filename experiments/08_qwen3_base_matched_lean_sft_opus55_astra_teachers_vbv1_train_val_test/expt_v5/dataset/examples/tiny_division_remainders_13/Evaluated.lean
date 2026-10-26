import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) : Bool := x % (n + 1) == 0
theorem spec_zero (n : Nat) : solution 0 n = true := by simp [solution]
theorem test_divisible : solution 6 2 = true := by norm_num [solution]
theorem test_not_divisible : solution (-7) 2 = false := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_zero
#print axioms Tiny.test_divisible
#print axioms Tiny.test_not_divisible

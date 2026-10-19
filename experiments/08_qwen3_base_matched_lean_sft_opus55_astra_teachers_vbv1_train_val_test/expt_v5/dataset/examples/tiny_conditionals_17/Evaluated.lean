import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) : Int := if x <= n then x else n
theorem spec_upper_bound (x : Int) (n : Nat) : solution x n <= n := by
  by_cases h : x <= n <;> simp [solution, h] <;> omega
theorem test_below : solution (-2) 3 = -2 := by decide
theorem test_above : solution 5 3 = 3 := by decide
end Tiny
#print axioms Tiny.spec_upper_bound
#print axioms Tiny.test_below
#print axioms Tiny.test_above

import Mathlib

namespace Tiny

def solution (x y z : Int) : Bool := decide (x ≤ y ∧ y < z)

theorem spec_true_iff (x y z : Int) : solution x y z = true ↔ x ≤ y ∧ y < z := by
  simp [solution]

theorem test_true : solution 1 1 2 = true := by
  decide

theorem test_last_false : solution 1 2 2 = false := by
  decide

end Tiny
#print axioms Tiny.spec_true_iff
#print axioms Tiny.test_true
#print axioms Tiny.test_last_false

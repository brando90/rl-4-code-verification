import Mathlib

namespace Tiny

def solution (x y z : Int) : Bool := decide (x ≤ y ∧ y ≤ z)

theorem spec_true_iff (x y z : Int) : solution x y z = true ↔ x ≤ y ∧ y ≤ z := by
  simp [solution]

theorem test_equal : solution 2 2 2 = true := by
  decide

theorem test_descending : solution 3 2 4 = false := by
  decide

end Tiny
#print axioms Tiny.spec_true_iff
#print axioms Tiny.test_equal
#print axioms Tiny.test_descending

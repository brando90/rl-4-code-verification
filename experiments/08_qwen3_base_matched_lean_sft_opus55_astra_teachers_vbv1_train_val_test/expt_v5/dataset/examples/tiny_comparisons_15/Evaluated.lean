import Mathlib

namespace Tiny

def solution (x y z : Int) : Bool := decide (x = y ∨ y = z)

theorem spec_true_iff (x y z : Int) : solution x y z = true ↔ x = y ∨ y = z := by
  simp [solution]

theorem test_first_pair : solution 2 2 3 = true := by
  decide

theorem test_none : solution 1 2 3 = false := by
  decide

end Tiny
#print axioms Tiny.spec_true_iff
#print axioms Tiny.test_first_pair
#print axioms Tiny.test_none

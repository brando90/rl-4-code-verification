import Mathlib

namespace Tiny

def solution (x y z : Int) : Bool := decide (x < y ∨ x > z)

theorem spec_true_iff (x y z : Int) : solution x y z = true ↔ x < y ∨ x > z := by
  simp [solution]

theorem test_left : solution 1 2 0 = true := by
  decide

theorem test_neither : solution 2 1 3 = false := by
  decide

end Tiny
#print axioms Tiny.spec_true_iff
#print axioms Tiny.test_left
#print axioms Tiny.test_neither

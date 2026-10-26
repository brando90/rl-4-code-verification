import Mathlib

namespace Tiny

def solution (x y : Int) : Bool := decide (x < y ∧ y < x)

theorem spec_true_iff (x y : Int) : solution x y = true ↔ x < y ∧ y < x := by
  simp [solution]

theorem test_increasing : solution 1 2 = false := by
  decide

theorem test_equal : solution (-3) (-3) = false := by
  decide

end Tiny
#print axioms Tiny.spec_true_iff
#print axioms Tiny.test_increasing
#print axioms Tiny.test_equal

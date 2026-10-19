import Mathlib
namespace Tiny
def solution : Nat → Int
  | 0 => 0
  | n + 1 => solution n + n
theorem spec_step (n : Nat) : solution (n + 1) = solution n + n := by rfl
theorem test_empty : solution 0 = 0 := by decide
theorem test_four : solution 4 = 6 := by decide
end Tiny
#print axioms Tiny.spec_step
#print axioms Tiny.test_empty
#print axioms Tiny.test_four

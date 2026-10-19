import Mathlib
namespace Tiny
def solution (n k : Nat) (xs : List Int) : Nat := (xs.drop n).take k |>.length
theorem spec_zero (k : Nat) (xs : List Int) : solution 0 k xs = (xs.take k).length := by rfl
theorem test_window : solution 1 2 [1, 2, 3, 4] = 2 := by decide
theorem test_past_end : solution 5 2 [1, 2] = 0 := by decide
end Tiny
#print axioms Tiny.spec_zero
#print axioms Tiny.test_window
#print axioms Tiny.test_past_end

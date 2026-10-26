import Mathlib
namespace Tiny
def solution (n : Nat) : Nat := n
theorem spec_value (n : Nat) : solution n = n := by rfl
theorem test_zero : solution 0 = 0 := by decide
theorem test_five : solution 5 = 5 := by decide
end Tiny

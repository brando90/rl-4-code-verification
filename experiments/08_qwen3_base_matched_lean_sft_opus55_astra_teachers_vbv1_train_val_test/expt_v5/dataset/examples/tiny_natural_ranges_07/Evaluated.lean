import Mathlib
namespace Tiny
def solution (_ : Nat) : Bool := false
theorem spec_not_member (n : Nat) : solution n = false := by rfl
theorem test_zero : solution 0 = false := by decide
theorem test_five : solution 5 = false := by decide
end Tiny
#print axioms Tiny.spec_not_member
#print axioms Tiny.test_zero
#print axioms Tiny.test_five

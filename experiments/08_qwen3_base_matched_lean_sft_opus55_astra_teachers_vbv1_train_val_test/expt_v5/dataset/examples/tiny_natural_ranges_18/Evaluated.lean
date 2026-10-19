import Mathlib
namespace Tiny
def solution (_ : Nat) : Bool := true
theorem spec_nonnegative (n : Nat) : solution n = true := by rfl
theorem test_empty : solution 0 = true := by decide
theorem test_nonempty : solution 5 = true := by decide
end Tiny
#print axioms Tiny.spec_nonnegative
#print axioms Tiny.test_empty
#print axioms Tiny.test_nonempty

import Mathlib
namespace Tiny
def solution (_ : Nat) : Bool := true
theorem spec_nonnegative (n : Nat) : solution n = true := by rfl
theorem test_empty : solution 0 = true := by decide
theorem test_nonempty : solution 5 = true := by decide
end Tiny

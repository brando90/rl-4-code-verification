import Mathlib
namespace Tiny
def solution (n k : Nat) : Bool := decide (k < n)
theorem spec_member (n k : Nat) : solution n k = true ↔ k < n := by simp [solution]
theorem test_member : solution 4 3 = true := by decide
theorem test_not_member : solution 4 4 = false := by decide
end Tiny
#print axioms Tiny.spec_member
#print axioms Tiny.test_member
#print axioms Tiny.test_not_member

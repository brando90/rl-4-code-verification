import Mathlib
namespace Tiny
def solution (p : Bool) : Bool := !(!p)
theorem spec_identity (p : Bool) : solution p = p := by
  cases p <;> decide
theorem test_true : solution true = true := by decide
theorem test_false : solution false = false := by decide
end Tiny
#print axioms Tiny.spec_identity
#print axioms Tiny.test_true
#print axioms Tiny.test_false

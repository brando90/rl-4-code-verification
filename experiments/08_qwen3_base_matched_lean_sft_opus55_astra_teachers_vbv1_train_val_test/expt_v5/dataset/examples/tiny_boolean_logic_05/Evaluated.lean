import Mathlib
namespace Tiny
def solution (p q : Bool) : Bool := p == q
theorem spec_same (p : Bool) : solution p p = true := by
  cases p <;> decide
theorem test_same : solution false false = true := by decide
theorem test_different : solution true false = false := by decide
end Tiny
#print axioms Tiny.spec_same
#print axioms Tiny.test_same
#print axioms Tiny.test_different

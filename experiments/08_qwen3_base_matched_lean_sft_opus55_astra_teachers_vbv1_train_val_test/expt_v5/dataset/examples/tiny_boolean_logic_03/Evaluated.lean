import Mathlib
namespace Tiny
def solution (p q : Bool) : Bool := p || q
theorem spec_commutative (p q : Bool) : solution p q = solution q p := by
  cases p <;> cases q <;> decide
theorem test_false_false : solution false false = false := by decide
theorem test_false_true : solution false true = true := by decide
end Tiny
#print axioms Tiny.spec_commutative
#print axioms Tiny.test_false_false
#print axioms Tiny.test_false_true

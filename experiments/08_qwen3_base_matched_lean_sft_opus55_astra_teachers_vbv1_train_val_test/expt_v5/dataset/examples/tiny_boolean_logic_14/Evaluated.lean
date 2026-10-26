import Mathlib
namespace Tiny
def solution (p q r : Bool) : Bool := if q then p else r
theorem spec_when_true (p r : Bool) : solution p true r = p := by
  rfl
theorem spec_when_false (p r : Bool) : solution p false r = r := by
  rfl
theorem test_select_first : solution true true false = true := by decide
theorem test_select_last : solution true false false = false := by decide
end Tiny
#print axioms Tiny.spec_when_true
#print axioms Tiny.spec_when_false
#print axioms Tiny.test_select_first
#print axioms Tiny.test_select_last

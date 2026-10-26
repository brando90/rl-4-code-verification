import Mathlib
namespace Tiny
def solution (p q r : Bool) : Bool := (!p || q) && (!q || r)
theorem spec_not_counterexamples (p q r : Bool) :
    solution p q r = (!(p && !q) && !(q && !r)) := by
  cases p <;> cases q <;> cases r <;> decide
theorem test_chain : solution true true true = true := by decide
theorem test_broken_chain : solution true false true = false := by decide
end Tiny

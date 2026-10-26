import Mathlib
namespace Tiny
def solution (p q : Bool) : Bool := !(p && q)
theorem spec_de_morgan (p q : Bool) : solution p q = (!p || !q) := by
  cases p <;> cases q <;> decide
theorem test_both_true : solution true true = false := by decide
theorem test_one_false : solution true false = true := by decide
end Tiny

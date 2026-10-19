import Mathlib
namespace Tiny
def solution (p q : Bool) : Bool := p && q
theorem spec_commutative (p q : Bool) : solution p q = solution q p := by
  cases p <;> cases q <;> decide
theorem test_true_true : solution true true = true := by decide
theorem test_true_false : solution true false = false := by decide
end Tiny

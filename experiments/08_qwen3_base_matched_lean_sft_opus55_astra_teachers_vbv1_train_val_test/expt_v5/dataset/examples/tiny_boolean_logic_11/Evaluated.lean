import Mathlib
namespace Tiny
def solution (p q r : Bool) : Bool := (p && q) || (p && r)
theorem spec_factor (p q r : Bool) : solution p q r = (p && (q || r)) := by
  cases p <;> cases q <;> cases r <;> decide
theorem test_true_false_true : solution true false true = true := by decide
theorem test_false_true_true : solution false true true = false := by decide
end Tiny
#print axioms Tiny.spec_factor
#print axioms Tiny.test_true_false_true
#print axioms Tiny.test_false_true_true
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true true)))

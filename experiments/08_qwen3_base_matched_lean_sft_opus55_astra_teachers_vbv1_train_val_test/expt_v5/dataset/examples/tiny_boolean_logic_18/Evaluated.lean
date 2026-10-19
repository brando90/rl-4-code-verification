import Mathlib
namespace Tiny
def solution (p q r : Bool) : Bool := (p == q) && (q == r)
theorem spec_endpoints (p q r : Bool) : solution p q r = ((p == q) && (p == r)) := by
  cases p <;> cases q <;> cases r <;> decide
theorem test_all_true : solution true true true = true := by decide
theorem test_one_different : solution true false false = false := by decide
end Tiny
#print axioms Tiny.spec_endpoints
#print axioms Tiny.test_all_true
#print axioms Tiny.test_one_different
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true true)))

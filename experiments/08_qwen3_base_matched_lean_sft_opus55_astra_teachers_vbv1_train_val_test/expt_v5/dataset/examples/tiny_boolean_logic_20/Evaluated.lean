import Mathlib
namespace Tiny
def solution (p q r : Bool) : Bool := (!p || q) && (!q || r)
theorem spec_not_counterexamples (p q r : Bool) :
    solution p q r = (!(p && !q) && !(q && !r)) := by
  cases p <;> cases q <;> cases r <;> decide
theorem test_chain : solution true true true = true := by decide
theorem test_broken_chain : solution true false true = false := by decide
end Tiny
#print axioms Tiny.spec_not_counterexamples
#print axioms Tiny.test_chain
#print axioms Tiny.test_broken_chain
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false true)))

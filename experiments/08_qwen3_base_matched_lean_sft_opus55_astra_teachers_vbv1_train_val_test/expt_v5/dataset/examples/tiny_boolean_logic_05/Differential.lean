import Mathlib
namespace Tiny
def solution (p q : Bool) : Bool := p == q
theorem spec_same (p : Bool) : solution p p = true := by
  cases p <;> decide
theorem test_same : solution false false = true := by decide
theorem test_different : solution true false = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true)))

import Mathlib
namespace Tiny
def solution (p q : Bool) : Bool := p != q
theorem spec_complement_eq (p q : Bool) : solution p q = !(p == q) := by
  cases p <;> cases q <;> decide
theorem test_same : solution true true = false := by decide
theorem test_different : solution true false = true := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false)))

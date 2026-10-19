import Mathlib
namespace Tiny
def solution (p : Bool) : Bool := p || false
theorem spec_identity (p : Bool) : solution p = p := by
  cases p <;> decide
theorem test_true : solution true = true := by decide
theorem test_false : solution false = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))

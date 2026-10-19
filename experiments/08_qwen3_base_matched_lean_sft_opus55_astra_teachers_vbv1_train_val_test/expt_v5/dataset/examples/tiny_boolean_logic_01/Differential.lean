import Mathlib
namespace Tiny
def solution (p : Bool) : Bool := !p
theorem spec_involutive (p : Bool) : solution (solution p) = p := by
  cases p <;> decide
theorem test_true : solution true = false := by decide
theorem test_false : solution false = true := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
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
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true)))

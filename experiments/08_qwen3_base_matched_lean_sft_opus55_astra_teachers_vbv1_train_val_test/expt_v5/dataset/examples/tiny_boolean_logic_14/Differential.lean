import Mathlib
namespace Tiny
def solution (p q r : Bool) : Bool := if q then p else r
theorem spec_when_true (p r : Bool) : solution p true r = p := by
  rfl
theorem spec_when_false (p r : Bool) : solution p false r = r := by
  rfl
theorem test_select_first : solution true true false = true := by decide
theorem test_select_last : solution true false false = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution false true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution true false true)))

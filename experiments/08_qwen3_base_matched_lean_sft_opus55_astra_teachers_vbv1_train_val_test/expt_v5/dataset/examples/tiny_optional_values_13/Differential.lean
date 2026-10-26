import Mathlib
namespace Tiny
def solution (opt : Option Int) : List Int := match opt with | none => [] | some x => [x]
theorem spec_some (x : Int) : solution (some x) = [x] := by rfl
theorem test_none : solution none = [] := by decide
theorem test_value : solution (some (-2)) = [-2] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (0) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-3) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (0) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-2) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (0) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (0) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-2) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-2) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-2) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (2) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-4) : Option Int))))

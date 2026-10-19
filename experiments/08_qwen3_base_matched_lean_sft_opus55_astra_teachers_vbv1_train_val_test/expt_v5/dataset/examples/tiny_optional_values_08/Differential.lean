import Mathlib
namespace Tiny
def solution (opt : Option Int) : Option Int := opt.map abs
theorem spec_some (x : Int) : solution (some x) = some (abs x) := by rfl
theorem test_none : solution none = none := by decide
theorem test_value : solution (some (-2)) = some 2 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (2) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-2) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (3) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-2) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-3) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (2) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (0) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-2) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (2) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (2) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (-3) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (some (0) : Option Int))))

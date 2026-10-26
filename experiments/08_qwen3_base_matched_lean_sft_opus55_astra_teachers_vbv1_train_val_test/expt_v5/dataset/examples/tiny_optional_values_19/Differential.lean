import Mathlib
namespace Tiny
def solution (x : Int) (p : Bool) (opt : Option Int) : Option Int := match opt with | some value => some value | none => if p then some x else none
theorem spec_some (x : Int) (p : Bool) (value : Int) : solution x p (some value) = some value := by rfl
theorem test_value : solution 3 false (some (-2)) = some (-2) := by decide
theorem test_fallback : solution 3 true none = some 3 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) false (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) true (some (-2) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) true (some (-4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) false (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) false (some (1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) false (some (0) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) true (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) false (some (-1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) false (some (-2) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) false (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) false (some (1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) true (some (0) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) true (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) false (some (-3) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) true (some (-4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) true (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) false (some (0) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) false (some (-3) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) true (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) false (some (2) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) false (some (3) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) true (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) false (some (-4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) true (some (4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) false (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) true (some (3) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) true (some (-3) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) true (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) false (some (4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) true (some (-1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) true (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) false (some (2) : Option Int))))

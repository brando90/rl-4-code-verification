import Mathlib
namespace Tiny
def solution (x : Int) (p : Bool) : Option Int := if p then some x else none
theorem spec_true (x : Int) : solution x true = some x := by rfl
theorem spec_false (x : Int) : solution x false = none := by rfl
theorem test_true : solution 3 true = some 3 := by decide
theorem test_false : solution (-3) false = none := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) true)))

import Mathlib
namespace Tiny
def solution (x : Int) (p : Bool) : Int := if p then x + 1 else x - 1
theorem spec_true (x : Int) : solution x true = x + 1 := by rfl
theorem test_true : solution 3 true = 4 := by decide
theorem test_false : solution 3 false = 2 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) true)))

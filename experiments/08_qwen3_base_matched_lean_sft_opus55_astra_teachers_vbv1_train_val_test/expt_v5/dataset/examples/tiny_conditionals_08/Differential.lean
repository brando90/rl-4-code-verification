import Mathlib
namespace Tiny
def solution (x y : Int) (p : Bool) : Int := if !p then x else y
theorem spec_false (x y : Int) : solution x y false = x := by rfl
theorem test_false : solution 4 9 false = 4 := by decide
theorem test_true : solution 4 9 true = 9 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-6) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-2) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (4) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-4) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-1) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-3) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (2) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-2) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-5) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-3) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (0) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-2) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-5) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-1) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-6) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (0) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-2) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (5) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-1) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6) true)))

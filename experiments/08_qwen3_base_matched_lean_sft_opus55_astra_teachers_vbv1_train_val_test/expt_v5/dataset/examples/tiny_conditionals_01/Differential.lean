import Mathlib
namespace Tiny
def solution (x y : Int) (p : Bool) : Int := if p then x else y
theorem spec_true (x y : Int) : solution x y true = x := by rfl
theorem test_true : solution 2 (-3) true = 2 := by decide
theorem test_false : solution 2 (-3) false = -3 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-4) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-3) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (0) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-2) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-3) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-3) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-4) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (6) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-3) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-2) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-2) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-5) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (4) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-3) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (6) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-5) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-4) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-1) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (5) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (0) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-4) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-1) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-5) true)))

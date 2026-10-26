import Mathlib
namespace Tiny
def solution (x y : Int) (p : Bool) : Int := if p then x + y else x - y
theorem spec_true (x y : Int) : solution x y true = x + y := by rfl
theorem test_sum : solution 4 (-2) true = 2 := by decide
theorem test_difference : solution 4 (-2) false = 6 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (5) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-3) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-6) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (3) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (5) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-6) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-4) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-5) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (0) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-1) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-5) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-2) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (0) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (3) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-6) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-3) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3) true)))

import Mathlib
namespace Tiny
def solution (x y : Int) : List Int := [x, y, x]
theorem spec_second (x y : Int) : (solution x y).get? 1 = some y := by simp [solution]
theorem test_order : solution 2 3 = [2, 3, 2] := by decide
theorem test_negative : solution (-1) 0 = [-1, 0, -1] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-6))))

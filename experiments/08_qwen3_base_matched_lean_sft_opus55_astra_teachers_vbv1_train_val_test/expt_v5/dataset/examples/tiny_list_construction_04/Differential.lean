import Mathlib
namespace Tiny
def solution (x y z : Int) : List Int := [x, y, z]
theorem spec_length (x y z : Int) : (solution x y z).length = 3 := by simp [solution]
theorem test_order : solution 1 2 3 = [1, 2, 3] := by decide
theorem test_negative : solution (-1) 0 2 = [-1, 0, 2] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-1) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-5) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-6) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-3) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-2) (-4))))

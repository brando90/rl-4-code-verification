import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := x * (y - z) + x * z

theorem spec_cancel (x y z : Int) : solution x y z = x * y := by
  simp [solution]
  ring

theorem test_positive : solution 2 3 4 = 6 := by decide
theorem test_negative : solution (-2) 3 (-5) = -6 := by decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (0) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (5) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) (-1))))

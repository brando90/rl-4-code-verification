import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := x * y + x * z

theorem spec_factor (x y z : Int) : solution x y z = x * (y + z) := by
  simp [solution]
  ring

theorem test_positive : solution 2 3 4 = 14 := by decide
theorem test_negative : solution (-2) 3 (-5) = 4 := by decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-1) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-5) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-5) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (0) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-3) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) (-3))))

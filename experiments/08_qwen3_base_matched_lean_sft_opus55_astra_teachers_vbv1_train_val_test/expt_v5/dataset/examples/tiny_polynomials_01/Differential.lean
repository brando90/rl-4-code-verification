import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := x * (y + z)

theorem spec_distribute (x y z : Int) : solution x y z = x * y + x * z := by
  simp [solution]
  ring

theorem test_positive : solution 2 3 4 = 14 := by decide
theorem test_negative : solution (-2) 3 (-5) = 4 := by decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (0) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (4) (-6))))

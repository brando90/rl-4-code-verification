import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := (x + y) * (y + z)

theorem spec_expand (x y z : Int) : solution x y z = x * y + x * z + y ^ 2 + y * z := by
  simp [solution]
  ring

theorem test_positive : solution 1 2 3 = 15 := by decide
theorem test_negative : solution (-2) 5 1 = 18 := by decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-5) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-3) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-1) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-5) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2) (5))))

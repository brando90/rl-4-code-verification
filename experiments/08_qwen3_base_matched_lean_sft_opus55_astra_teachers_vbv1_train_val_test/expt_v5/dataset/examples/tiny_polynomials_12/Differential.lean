import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := (x + y + z) ^ 2

theorem spec_expand (x y z : Int) :
    solution x y z = x ^ 2 + y ^ 2 + z ^ 2 + 2 * x * y + 2 * x * z + 2 * y * z := by
  simp [solution]
  ring

theorem test_positive : solution 1 2 3 = 36 := by decide
theorem test_negative : solution (-2) 5 1 = 16 := by decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-5) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (5) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-6) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-2) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2) (1))))

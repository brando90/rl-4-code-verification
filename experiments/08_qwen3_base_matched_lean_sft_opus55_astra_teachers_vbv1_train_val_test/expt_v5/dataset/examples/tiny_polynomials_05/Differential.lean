import Mathlib

namespace Tiny

def solution (x y : Int) : Int := (x + y) ^ 2

theorem spec_binomial (x y : Int) : solution x y = x ^ 2 + 2 * x * y + y ^ 2 := by
  simp [solution]
  ring

theorem test_positive : solution 2 3 = 25 := by decide
theorem test_negative : solution (-4) 1 = 9 := by decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4))))

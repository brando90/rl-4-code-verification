import Mathlib

namespace Tiny

def solution (x y : Int) : Int := (x + y) ^ 3

theorem spec_binomial (x y : Int) :
    solution x y = x ^ 3 + 3 * x ^ 2 * y + 3 * x * y ^ 2 + y ^ 3 := by
  simp [solution]
  ring

theorem test_positive : solution 1 2 = 27 := by decide
theorem test_negative : solution (-3) 1 = -8 := by decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-5))))

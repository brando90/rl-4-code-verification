import Mathlib
namespace Tiny
def solution (x y : Int) : Int := x - x * y
theorem spec_factored (x y : Int) : solution x y = x * (1 - y) := by
  simp only [solution]
  ring
theorem test_positive : solution 5 2 = -5 := by norm_num [solution]
theorem test_negative : solution (-3) 2 = 3 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (1))))

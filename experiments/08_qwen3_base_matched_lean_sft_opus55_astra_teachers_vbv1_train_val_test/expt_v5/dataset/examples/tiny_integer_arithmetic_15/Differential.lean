import Mathlib
namespace Tiny
def solution (x y : Int) : Int := x * (y + 1)
theorem spec_expand (x y : Int) : solution x y = x * y + x := by
  simp only [solution]
  ring
theorem test_positive : solution 3 4 = 15 := by norm_num [solution]
theorem test_negative : solution (-2) 3 = -8 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-1))))

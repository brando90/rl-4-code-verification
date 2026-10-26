import Mathlib

namespace Tiny

def solution (x y : Int) : Int := abs (x - y)

theorem spec_nonnegative (x y : Int) : 0 ≤ solution x y := by
  exact abs_nonneg (x - y)

theorem test_increasing : solution 2 7 = 5 := by norm_num [solution]
theorem test_decreasing : solution 7 2 = 5 := by norm_num [solution]

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-1))))

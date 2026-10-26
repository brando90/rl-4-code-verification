import Mathlib

namespace Tiny

def solution (x y : Int) : Int := max (-x) (-y)

theorem spec_left_le (x y : Int) : -x ≤ solution x y := by
  exact le_max_left (-x) (-y)

theorem test_first : solution 2 7 = -2 := by norm_num [solution]
theorem test_second : solution (-3) 1 = 3 := by norm_num [solution]

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-6))))

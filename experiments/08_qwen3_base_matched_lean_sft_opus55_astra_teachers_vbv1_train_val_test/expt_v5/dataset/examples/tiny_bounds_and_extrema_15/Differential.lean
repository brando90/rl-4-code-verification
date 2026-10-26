import Mathlib

namespace Tiny

def solution (x y : Int) : Int := min (abs x) (abs y)

theorem spec_le_left (x y : Int) : solution x y ≤ abs x := by
  exact min_le_left (abs x) (abs y)

theorem test_first : solution (-2) 7 = 2 := by norm_num [solution]
theorem test_second : solution (-8) 3 = 3 := by norm_num [solution]

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6))))

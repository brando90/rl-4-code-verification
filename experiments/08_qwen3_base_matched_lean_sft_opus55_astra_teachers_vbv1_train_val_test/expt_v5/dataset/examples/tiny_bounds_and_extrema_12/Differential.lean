import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := max (x + z) (y + z)

theorem spec_left_le (x y z : Int) : x + z ≤ solution x y z := by
  exact le_max_left (x + z) (y + z)

theorem test_left_largest : solution 7 2 (-3) = 4 := by norm_num [solution]
theorem test_right_largest : solution 2 7 (-3) = 4 := by norm_num [solution]

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-3) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (6) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-5) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-2) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-1) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-5) (-5))))

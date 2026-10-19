import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := min (x + z) (y + z)

theorem spec_le_left (x y z : Int) : solution x y z ≤ x + z := by
  exact min_le_left (x + z) (y + z)

theorem test_left_smallest : solution 2 7 (-3) = -1 := by norm_num [solution]
theorem test_right_smallest : solution 7 2 (-3) = -1 := by norm_num [solution]

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (0) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (6) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-3) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-5) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-4) (6))))

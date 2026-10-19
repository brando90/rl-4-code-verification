import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := min (min x y) z

theorem spec_le_first (x y z : Int) : solution x y z ≤ x := by
  exact le_trans (min_le_left (min x y) z) (min_le_left x y)

theorem test_last_smallest : solution 3 2 (-1) = -1 := by norm_num [solution]
theorem test_first_smallest : solution (-4) 2 1 = -4 := by norm_num [solution]

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (0) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (0) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4) (-2))))

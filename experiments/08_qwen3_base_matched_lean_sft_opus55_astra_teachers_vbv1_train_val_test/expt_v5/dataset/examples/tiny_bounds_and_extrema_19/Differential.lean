import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := min (max x y) (max x z)

theorem spec_le_left (x y z : Int) : solution x y z ≤ max x y := by
  exact min_le_left (max x y) (max x z)

theorem test_common : solution 2 7 3 = 3 := by norm_num [solution]
theorem test_first : solution 9 7 3 = 9 := by norm_num [solution]

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (0) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-5) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-2) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) (3))))

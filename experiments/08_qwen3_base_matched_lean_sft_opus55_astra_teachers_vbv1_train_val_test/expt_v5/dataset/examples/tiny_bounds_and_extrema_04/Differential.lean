import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := max (max x y) z

theorem spec_first_le (x y z : Int) : x ≤ solution x y z := by
  exact le_trans (le_max_left x y) (le_max_left (max x y) z)

theorem test_last_largest : solution 3 2 9 = 9 := by norm_num [solution]
theorem test_first_largest : solution 4 2 (-1) = 4 := by norm_num [solution]

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-3) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-1) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-3) (-1))))

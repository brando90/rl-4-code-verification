import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := max x (min y z)

theorem spec_first_le (x y z : Int) : x ≤ solution x y z := by
  exact le_max_left x (min y z)

theorem test_first : solution 9 7 3 = 9 := by norm_num [solution]
theorem test_inner : solution 2 7 3 = 3 := by norm_num [solution]

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (2) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-6) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (5) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-1) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (0) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (-1))))

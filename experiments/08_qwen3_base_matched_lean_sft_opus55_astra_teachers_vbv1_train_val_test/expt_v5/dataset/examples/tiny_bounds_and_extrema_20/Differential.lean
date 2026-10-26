import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := max (min x y) (min x z)

theorem spec_left_le (x y z : Int) : min x y ≤ solution x y z := by
  exact le_max_left (min x y) (min x z)

theorem test_common : solution 2 7 3 = 2 := by norm_num [solution]
theorem test_first : solution 9 7 3 = 7 := by norm_num [solution]

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-1) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-5) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (0) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (0) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-5) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (5) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-4) (-5))))

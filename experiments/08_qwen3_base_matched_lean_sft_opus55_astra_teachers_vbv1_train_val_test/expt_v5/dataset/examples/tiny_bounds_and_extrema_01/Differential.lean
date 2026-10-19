import Mathlib

namespace Tiny

def solution (x y : Int) : Int := min x y

theorem spec_le_left (x y : Int) : solution x y ≤ x := by
  exact min_le_left x y

theorem test_negative : solution (-3) 2 = -3 := by norm_num [solution]
theorem test_order : solution 7 4 = 4 := by norm_num [solution]

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5))))

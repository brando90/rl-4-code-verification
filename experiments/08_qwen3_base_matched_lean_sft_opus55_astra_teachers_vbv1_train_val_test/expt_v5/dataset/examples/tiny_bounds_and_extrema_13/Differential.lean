import Mathlib

namespace Tiny

def solution (x y : Int) : Int := min (-x) (-y)

theorem spec_le_left (x y : Int) : solution x y ≤ -x := by
  exact min_le_left (-x) (-y)

theorem test_first : solution 2 7 = -7 := by norm_num [solution]
theorem test_second : solution (-3) 1 = -1 := by norm_num [solution]

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4))))

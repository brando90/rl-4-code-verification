import Mathlib

namespace Tiny

def solution (x y : Int) : Int := max x y - min x y

theorem spec_nonnegative (x y : Int) : 0 ≤ solution x y := by
  exact sub_nonneg.mpr min_le_max

theorem test_increasing : solution 2 7 = 5 := by norm_num [solution]
theorem test_decreasing : solution 7 2 = 5 := by norm_num [solution]

end Tiny
#print axioms Tiny.spec_nonnegative
#print axioms Tiny.test_increasing
#print axioms Tiny.test_decreasing
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (1))))

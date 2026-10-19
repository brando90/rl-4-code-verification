import Mathlib
namespace Tiny
def solution (x y z : Int) : Int := x + y - z
theorem spec_add_z (x y z : Int) : solution x y z + z = x + y := by
  simp [solution]
theorem test_positive : solution 4 5 3 = 6 := by norm_num [solution]
theorem test_negative : solution (-2) 1 4 = -5 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (5) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (0) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-5) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (0) (-4))))

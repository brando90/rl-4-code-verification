import Mathlib
namespace Tiny
def solution (x y z : Int) : Int := x + y + z
theorem spec_reverse (x y z : Int) : solution x y z = solution z y x := by
  simp [solution, add_comm, add_left_comm]
theorem test_positive : solution 1 2 3 = 6 := by norm_num [solution]
theorem test_negative : solution (-4) 1 2 = -1 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (6) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (5) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-2) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (3) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-5) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (0) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (6) (5))))

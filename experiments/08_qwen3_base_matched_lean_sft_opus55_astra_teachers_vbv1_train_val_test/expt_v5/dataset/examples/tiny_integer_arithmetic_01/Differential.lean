import Mathlib
namespace Tiny
def solution (x y : Int) : Int := x + y
theorem spec_commutative (x y : Int) : solution x y = solution y x := by
  simp [solution, add_comm]
theorem test_positive : solution 2 3 = 5 := by norm_num [solution]
theorem test_negative : solution (-3) 1 = -2 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-2))))

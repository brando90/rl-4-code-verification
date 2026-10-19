import Mathlib
namespace Tiny
def solution (x y : Int) : Int := |x - y|
theorem spec_symmetric (x y : Int) : solution x y = solution y x := by
  simp [solution, abs_sub_comm]
theorem test_positive : solution 7 3 = 4 := by norm_num [solution]
theorem test_negative : solution (-2) 5 = 7 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-6))))

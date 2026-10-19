import Mathlib
namespace Tiny
def solution (x y z : Int) : Int := x * y - x * z
theorem spec_factored (x y z : Int) : solution x y z = x * (y - z) := by
  simp only [solution]
  ring
theorem test_positive : solution 3 5 2 = 9 := by norm_num [solution]
theorem test_negative : solution (-2) 1 4 = 6 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_factored
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (0) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (1) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (0) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-1) (-4))))

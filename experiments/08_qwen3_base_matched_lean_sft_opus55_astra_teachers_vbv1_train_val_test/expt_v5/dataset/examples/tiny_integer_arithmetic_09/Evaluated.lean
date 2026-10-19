import Mathlib
namespace Tiny
def solution (x y z : Int) : Int := x * (y - z)
theorem spec_distributive (x y z : Int) : solution x y z = x * y - x * z := by
  simp only [solution]
  ring
theorem test_positive : solution 3 5 2 = 9 := by norm_num [solution]
theorem test_negative : solution (-2) 1 4 = 6 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_distributive
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (5) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-5) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-1) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (1) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-5) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-5) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-4) (-6))))

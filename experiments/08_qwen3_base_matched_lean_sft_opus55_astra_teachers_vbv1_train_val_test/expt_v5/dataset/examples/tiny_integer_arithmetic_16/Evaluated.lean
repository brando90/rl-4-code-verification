import Mathlib
namespace Tiny
def solution (x y : Int) : Int := x + -y
theorem spec_subtract (x y : Int) : solution x y = x - y := by
  simp [solution, sub_eq_add_neg]
theorem test_positive : solution 7 3 = 4 := by norm_num [solution]
theorem test_negative : solution (-3) 2 = -5 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_subtract
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1))))

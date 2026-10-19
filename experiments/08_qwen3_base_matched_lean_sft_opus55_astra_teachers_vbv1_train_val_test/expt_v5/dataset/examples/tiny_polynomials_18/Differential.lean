import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := x * (y * z)

theorem spec_associative (x y z : Int) : solution x y z = x * y * z := by
  simp [solution, mul_assoc]

theorem test_positive : solution 2 3 4 = 24 := by decide
theorem test_negative : solution (-2) 3 (-4) = 24 := by decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (0) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-6) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (1) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-5) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-5) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-2) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-2) (-3))))

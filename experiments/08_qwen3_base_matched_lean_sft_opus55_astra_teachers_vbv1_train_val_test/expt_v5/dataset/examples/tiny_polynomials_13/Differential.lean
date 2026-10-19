import Mathlib

namespace Tiny

def solution (x y z : Int) : Int := x * y + y * z + z * x

theorem spec_symmetric (x y z : Int) : solution x y z = solution y x z := by
  simp [solution]
  ring

theorem test_positive : solution 1 2 3 = 11 := by decide
theorem test_negative : solution (-2) 5 1 = -7 := by decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-5) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-3) (-6))))

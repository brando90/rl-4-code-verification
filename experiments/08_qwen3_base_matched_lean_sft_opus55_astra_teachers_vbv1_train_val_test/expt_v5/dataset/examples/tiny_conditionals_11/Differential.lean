import Mathlib
namespace Tiny
def solution (x y : Int) : Int := if x != 0 then x else y
theorem spec_nonzero (x y : Int) (h : x != 0) : solution x y = x := by
  simp [solution, h]
theorem test_nonzero : solution 3 9 = 3 := by decide
theorem test_zero : solution 0 9 = 9 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1))))

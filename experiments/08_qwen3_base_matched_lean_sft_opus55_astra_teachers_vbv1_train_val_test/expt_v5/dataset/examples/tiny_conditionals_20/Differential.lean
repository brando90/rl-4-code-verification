import Mathlib
namespace Tiny
def solution (x y z : Int) : Int := if x <= y && x <= z then x else min y z
theorem spec_smallest (x y z : Int) (h₁ : x <= y) (h₂ : x <= z) : solution x y z = x := by
  simp [solution, h₁, h₂]
theorem test_first : solution 1 5 3 = 1 := by decide
theorem test_other : solution 5 1 3 = 1 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (5) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-5) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) (-4))))

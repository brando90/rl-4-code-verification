import Mathlib
namespace Tiny
def solution (x y z : Int) : Int := if x >= y && x >= z then x else max y z
theorem spec_largest (x y z : Int) (h₁ : x >= y) (h₂ : x >= z) : solution x y z = x := by
  simp [solution, h₁, h₂]
theorem test_first : solution 5 2 3 = 5 := by decide
theorem test_other : solution 1 5 3 = 5 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (0) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (5) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (0) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (0) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (0) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (0) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-5) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-1) (-1))))

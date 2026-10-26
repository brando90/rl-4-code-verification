import Mathlib

namespace Tiny

def solution (x y z : Int) : Bool := decide (x < y ∨ x > z)

theorem spec_true_iff (x y z : Int) : solution x y z = true ↔ x < y ∨ x > z := by
  simp [solution]

theorem test_left : solution 1 2 0 = true := by
  decide

theorem test_neither : solution 2 1 3 = false := by
  decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-3) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-1) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-6) (-2))))

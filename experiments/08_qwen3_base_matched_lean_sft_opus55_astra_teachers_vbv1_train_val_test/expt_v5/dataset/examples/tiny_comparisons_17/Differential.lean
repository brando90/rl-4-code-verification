import Mathlib

namespace Tiny

def solution (x y z : Int) : Bool := decide (x + y ≤ z)

theorem spec_true_iff (x y z : Int) : solution x y z = true ↔ x + y ≤ z := by
  simp [solution]

theorem test_equal_sum : solution 2 3 5 = true := by
  decide

theorem test_too_large : solution (-1) 4 2 = false := by
  decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (5) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-2) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-2) (-4))))

import Mathlib

namespace Tiny

def solution (x y z : Int) : Bool := decide (x ≤ y ∧ y < z)

theorem spec_true_iff (x y z : Int) : solution x y z = true ↔ x ≤ y ∧ y < z := by
  simp [solution]

theorem test_true : solution 1 1 2 = true := by
  decide

theorem test_last_false : solution 1 2 2 = false := by
  decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (6) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-2) (5))))

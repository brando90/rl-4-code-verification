import Mathlib

namespace Tiny

def solution (x y z : Int) : Bool := decide (x < y ∧ y ≤ z)

theorem spec_true_iff (x y z : Int) : solution x y z = true ↔ x < y ∧ y ≤ z := by
  simp [solution]

theorem test_true : solution 1 2 2 = true := by
  decide

theorem test_first_false : solution 2 2 3 = false := by
  decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (5) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-1) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (0) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-3) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-3) (1))))

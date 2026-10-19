import Mathlib

namespace Tiny

def solution (x y z : Int) : Bool := decide (x ≤ y ∧ y ≤ z)

theorem spec_true_iff (x y z : Int) : solution x y z = true ↔ x ≤ y ∧ y ≤ z := by
  simp [solution]

theorem test_equal : solution 2 2 2 = true := by
  decide

theorem test_descending : solution 3 2 4 = false := by
  decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-2) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (0) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1) (2))))

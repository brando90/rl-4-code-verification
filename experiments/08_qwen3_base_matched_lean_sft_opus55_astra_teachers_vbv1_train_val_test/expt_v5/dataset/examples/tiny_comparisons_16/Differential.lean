import Mathlib

namespace Tiny

def solution (x y z : Int) : Bool := decide (x ≠ y ∧ y ≠ z)

theorem spec_true_iff (x y z : Int) : solution x y z = true ↔ x ≠ y ∧ y ≠ z := by
  simp [solution]

theorem test_all_adjacent_different : solution 1 2 1 = true := by
  decide

theorem test_first_pair_same : solution (-1) (-1) 2 = false := by
  decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-6) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-3) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (0) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-5) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (-6))))

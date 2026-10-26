import Mathlib

namespace Tiny

def solution (x y z : Int) : Bool := decide (x = y ∧ y = z)

theorem spec_true_iff (x y z : Int) : solution x y z = true ↔ x = y ∧ y = z := by
  simp [solution]

theorem test_all_same : solution (-1) (-1) (-1) = true := by
  decide

theorem test_one_different : solution 1 1 2 = false := by
  decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-5) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (0) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-6) (-4))))

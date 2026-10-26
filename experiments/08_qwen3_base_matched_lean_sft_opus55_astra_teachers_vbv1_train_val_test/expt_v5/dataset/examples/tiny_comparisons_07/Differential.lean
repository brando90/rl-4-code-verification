import Mathlib

namespace Tiny

def solution (x y z : Int) : Bool := decide (x < y ∧ y < z)

theorem spec_true_iff (x y z : Int) : solution x y z = true ↔ x < y ∧ y < z := by
  simp [solution]

theorem test_increasing : solution (-1) 0 2 = true := by
  decide

theorem test_equal_end : solution 1 2 2 = false := by
  decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (2) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-2) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (0) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (0) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-1) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (0) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (0) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (4) (3))))

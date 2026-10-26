import Mathlib

namespace Tiny

def solution (x y z : Int) : Bool := decide (x = y ∨ y = z)

theorem spec_true_iff (x y z : Int) : solution x y z = true ↔ x = y ∨ y = z := by
  simp [solution]

theorem test_first_pair : solution 2 2 3 = true := by
  decide

theorem test_none : solution 1 2 3 = false := by
  decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-3) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-6) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (0) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (0) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (0) (2))))

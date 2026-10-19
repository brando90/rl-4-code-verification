import Mathlib

namespace Tiny

def solution (x y z : Int) : Bool := decide (x - y < z)

theorem spec_true_iff (x y z : Int) : solution x y z = true ↔ x - y < z := by
  simp [solution]

theorem test_true : solution 1 3 (-1) = true := by
  decide

theorem test_equal : solution 5 2 3 = false := by
  decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (5) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (5) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (5) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-3) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-1) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) (5))))

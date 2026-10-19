import Mathlib

namespace Tiny

def solution (x y : Int) : Bool := decide (|x| ≤ y)

theorem spec_true_iff (x y : Int) : solution x y = true ↔ |x| ≤ y := by
  simp [solution]

theorem test_enough : solution (-3) 3 = true := by
  decide

theorem test_too_small : solution (-3) 2 = false := by
  decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0))))

import Mathlib

namespace Tiny

def solution (x y : Int) : Bool := decide (x ≤ y ∨ y ≤ x)

theorem spec_true_iff (x y : Int) : solution x y = true ↔ x ≤ y ∨ y ≤ x := by
  simp [solution]

theorem test_forward : solution (-3) 1 = true := by
  decide

theorem test_reverse : solution 4 (-2) = true := by
  decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-2))))

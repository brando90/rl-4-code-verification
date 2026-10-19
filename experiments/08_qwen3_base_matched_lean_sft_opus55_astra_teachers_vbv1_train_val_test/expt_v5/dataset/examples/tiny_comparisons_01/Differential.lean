import Mathlib

namespace Tiny

def solution (x y : Int) : Bool := decide (x < y)

theorem spec_true_iff (x y : Int) : solution x y = true ↔ x < y := by
  simp [solution]

theorem test_increasing : solution 2 3 = true := by
  decide

theorem test_equal : solution (-4) (-4) = false := by
  decide

end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3))))

import Mathlib
namespace Tiny
def solution (x y : Int) : Bool := x % 2 == y % 2
theorem spec_self (x : Int) : solution x x = true := by simp [solution]
theorem test_same_parity : solution (-3) 5 = true := by decide
theorem test_different_parity : solution 2 5 = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (3))))

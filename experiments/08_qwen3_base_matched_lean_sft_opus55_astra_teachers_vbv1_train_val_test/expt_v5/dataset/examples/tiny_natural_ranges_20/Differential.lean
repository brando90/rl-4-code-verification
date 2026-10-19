import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) : Int := n * x
theorem spec_zero (x : Int) : solution x 0 = 0 := by simp [solution]
theorem spec_step (x : Int) (n : Nat) : solution x (n + 1) = solution x n + x := by
  simp [solution, add_mul]
theorem test_zero : solution 7 0 = 0 := by decide
theorem test_negative : solution (-3) 4 = -12 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4))))

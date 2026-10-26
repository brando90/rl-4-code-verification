import Mathlib
namespace Tiny
def solution (x y z : Nat) : Nat := x * y + z
theorem spec_swap_factors (x y z : Nat) : solution x y z = y * x + z := by
  simp [solution, Nat.mul_comm]
theorem test_small : solution 2 3 4 = 10 := by norm_num [solution]
theorem test_zero : solution 0 3 4 = 4 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) (3))))

import Mathlib
namespace Tiny
def solution (x y z : Nat) : Nat := (x + y) * z
theorem spec_swap_factor (x y z : Nat) : solution x y z = z * (x + y) := by
  simp [solution, Nat.mul_comm]
theorem test_small : solution 2 3 4 = 20 := by norm_num [solution]
theorem test_zero : solution 2 3 0 = 0 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (0) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (3) (1))))

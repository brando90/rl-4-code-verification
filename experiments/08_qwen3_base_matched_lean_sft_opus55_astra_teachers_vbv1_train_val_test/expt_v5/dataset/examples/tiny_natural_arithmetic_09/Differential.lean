import Mathlib
namespace Tiny
def solution (x y z : Nat) : Nat := x + y * z
theorem spec_reorder (x y z : Nat) : solution x y z = z * y + x := by
  simp [solution, Nat.add_comm, Nat.mul_comm]
theorem test_small : solution 2 3 4 = 14 := by norm_num [solution]
theorem test_zero : solution 2 0 4 = 2 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (0) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (0) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1) (6))))

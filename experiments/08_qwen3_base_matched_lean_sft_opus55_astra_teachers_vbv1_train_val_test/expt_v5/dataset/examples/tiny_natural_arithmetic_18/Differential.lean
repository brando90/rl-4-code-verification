import Mathlib
namespace Tiny
def solution (x y z : Nat) : Nat := max (x + y) z
theorem spec_right_iff (x y z : Nat) : solution x y z = z ↔ x + y ≤ z := by
  simp [solution]
theorem test_sum : solution 2 3 9 = 9 := by norm_num [solution]
theorem test_floor : solution 5 6 7 = 11 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) (5))))

import Mathlib
namespace Tiny
def solution (x y z : Nat) : Nat := min (x + y) z
theorem spec_left_iff (x y z : Nat) : solution x y z = x + y ↔ x + y ≤ z := by
  simp [solution]
theorem test_sum : solution 2 3 9 = 5 := by norm_num [solution]
theorem test_cap : solution 5 6 7 = 7 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (6) (2))))

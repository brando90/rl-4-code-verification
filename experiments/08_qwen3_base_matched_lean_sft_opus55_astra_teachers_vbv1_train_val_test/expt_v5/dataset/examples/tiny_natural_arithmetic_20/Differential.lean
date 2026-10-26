import Mathlib
namespace Tiny
def solution (x y z : Nat) : Nat := x - min y z
theorem spec_first (x y z : Nat) (h : y ≤ z) : solution x y z = x - y := by
  simp [solution, h]
theorem test_positive : solution 10 3 6 = 7 := by norm_num [solution]
theorem test_clamped : solution 3 4 1 = 2 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) (1))))

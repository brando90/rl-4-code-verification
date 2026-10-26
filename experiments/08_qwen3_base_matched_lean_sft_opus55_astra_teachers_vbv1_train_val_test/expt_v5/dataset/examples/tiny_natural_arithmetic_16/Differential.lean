import Mathlib
namespace Tiny
def solution (x y z : Nat) : Nat := x - y - z
theorem spec_combined (x y z : Nat) : solution x y z = x - (y + z) := by
  simp [solution, Nat.sub_sub]
theorem test_positive : solution 10 3 2 = 5 := by norm_num [solution]
theorem test_clamped : solution 3 2 4 = 0 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) (1))))

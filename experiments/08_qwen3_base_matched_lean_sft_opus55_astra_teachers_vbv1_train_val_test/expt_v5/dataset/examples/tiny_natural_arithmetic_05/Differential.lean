import Mathlib
namespace Tiny
def solution (x y z : Nat) : Nat := x + y + z
theorem spec_swap (x y z : Nat) : solution x y z = solution y x z := by
  simp [solution, Nat.add_comm]
theorem test_small : solution 2 3 4 = 9 := by norm_num [solution]
theorem test_zero : solution 0 0 7 = 7 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) (5))))

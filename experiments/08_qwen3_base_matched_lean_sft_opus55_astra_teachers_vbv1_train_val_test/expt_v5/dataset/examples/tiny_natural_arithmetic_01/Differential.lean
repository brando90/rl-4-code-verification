import Mathlib
namespace Tiny
def solution (x y : Nat) : Nat := x + y
theorem spec_commutative (x y : Nat) : solution x y = solution y x := by
  simp [solution, Nat.add_comm]
theorem test_small : solution 2 3 = 5 := by norm_num [solution]
theorem test_zero : solution 0 7 = 7 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2))))

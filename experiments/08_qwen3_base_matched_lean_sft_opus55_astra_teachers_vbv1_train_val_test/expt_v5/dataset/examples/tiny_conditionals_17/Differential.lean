import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) : Int := if x <= n then x else n
theorem spec_upper_bound (x : Int) (n : Nat) : solution x n <= n := by
  by_cases h : x <= n <;> simp [solution, h] <;> omega
theorem test_below : solution (-2) 3 = -2 := by decide
theorem test_above : solution 5 3 = 3 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (3))))

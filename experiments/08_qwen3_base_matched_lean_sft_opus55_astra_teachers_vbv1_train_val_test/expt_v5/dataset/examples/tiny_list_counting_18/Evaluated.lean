import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs : List Int) : Nat := n * xs.count x
theorem spec_succ (x : Int) (n : Nat) (xs : List Int) :
    solution x (n + 1) xs = solution x n xs + xs.count x := by simp [solution, Nat.add_mul]
theorem test_repeated : solution 2 3 [2, 1, 2] = 6 := by decide
theorem test_zero : solution 2 0 [2, 1] = 0 := by decide
end Tiny
#print axioms Tiny.spec_succ
#print axioms Tiny.test_repeated
#print axioms Tiny.test_zero
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (1) [(1), (-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) [(1), (0), (3), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (1) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) [(0), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6) [(3), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (5) [(4), (4), (-3), (-1), (3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) [(1), (-1), (1), (4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3) [(-2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) [(-3), (-4), (-3), (3), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (3) [(-1), (-1), (-2), (0), (4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (5) [(-3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (2) [(4), (-3), (-4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (6) [(2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1) [(-2), (4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (6) [(-2), (-2), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (1) [(-2), (-3), (-2), (-2), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (5) [(4), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) [(-2), (-4), (4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) [(1), (-3), (-3), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (3) [(-1), (0), (-2), (1)])))

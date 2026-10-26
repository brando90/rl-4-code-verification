import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : Int := (xs.drop n).sum
theorem spec_cons_succ (n : Nat) (x : Int) (xs : List Int) : solution (n + 1) (x :: xs) = solution n xs := by rfl
theorem test_empty : solution 3 [] = 0 := by decide
theorem test_suffix : solution 2 [3, -5, 2] = 2 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-2), (-3), (-4), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(0), (3), (-2), (-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(3), (4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(3), (4), (1), (-2), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-2), (-3), (1), (-3), (4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(2), (-4), (-4), (3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-1), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(2), (1), (2), (-1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-1), (-1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(2), (4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-4), (-4), (-1), (2), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(4), (-4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-1), (3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-2), (-1), (0), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(3), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(4), (1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-3), (4), (4), (4), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-2), (0), (-1), (2), (3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-4), (2), (-3), (-1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(2), (-2)])))

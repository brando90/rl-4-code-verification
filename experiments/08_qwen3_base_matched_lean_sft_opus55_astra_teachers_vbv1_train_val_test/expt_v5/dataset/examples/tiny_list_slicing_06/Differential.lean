import Mathlib
namespace Tiny
def solution (n k : Nat) (xs : List Int) : List Int := (xs.drop n).drop k
theorem spec_zero (k : Nat) (xs : List Int) : solution 0 k xs = xs.drop k := by rfl
theorem test_drops : solution 1 2 [1, 2, 3, 4] = [4] := by decide
theorem test_past_end : solution 5 1 [1, 2] = [] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) [(-4), (2), (-3), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) [(-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) [(0), (2), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) [(4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4) [(0), (2), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1) [(2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) [(0), (4), (-3), (-3), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) [(-2), (4), (4), (4), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) [(-4), (0), (2), (1), (4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) [(2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) [(-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4) [(-1), (-3), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) [(4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) [(-4), (-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) [(-2), (-1), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) [(4), (0), (4), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (6) [(0), (-2), (-1), (-4), (-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) [(0), (-2), (-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) [(-4), (-3), (-4), (1), (3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) [(1), (3), (-1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) [(-1), (1), (-3), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) [(2), (3), (1), (-2), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) [(-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) [(-1), (0), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) [(-2), (4), (4), (1), (-2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5) [(0), (4), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (3) [(0), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) [(4), (1), (3), (-1), (0)])))

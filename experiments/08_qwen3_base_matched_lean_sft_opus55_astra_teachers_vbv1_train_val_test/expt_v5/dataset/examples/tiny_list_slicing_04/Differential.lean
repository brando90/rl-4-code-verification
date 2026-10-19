import Mathlib
namespace Tiny
def solution (n k : Nat) (xs : List Int) : List Int := (xs.drop n).take k
theorem spec_zero (k : Nat) (xs : List Int) : solution 0 k xs = xs.take k := by rfl
theorem test_window : solution 1 2 [1, 2, 3, 4] = [2, 3] := by decide
theorem test_past_end : solution 5 2 [1, 2] = [] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) [(2), (1), (-4), (3), (4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) [(-2), (0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5) [(-1), (3), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (6) [(-1), (-1), (-3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) [(-1), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) [(2), (1), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) [(0), (3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) [(-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) [(-1), (-2), (4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) [(1), (-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) [(3), (3), (-3), (0), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) [(-3), (3), (-3), (1), (4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) [(-4), (0), (2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) [(0), (-4), (1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (0) [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (5) [(-4), (-1), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) [(-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) [(4), (3), (3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) [(0), (0), (0), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) [(-2), (-1), (1), (-1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (5) [(3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) [(-1), (-3), (0), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1) [(2), (0), (-4), (4), (-1)])))

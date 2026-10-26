import Mathlib
namespace Tiny
def solution (n k : Nat) (xs : List Int) : Nat := (xs.drop n).take k |>.length
theorem spec_zero (k : Nat) (xs : List Int) : solution 0 k xs = (xs.take k).length := by rfl
theorem test_window : solution 1 2 [1, 2, 3, 4] = 2 := by decide
theorem test_past_end : solution 5 2 [1, 2] = 0 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) [(-4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) [(2), (-1), (-3), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (6) [(1), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (3) [(3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) [(0), (3), (2), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) [(-1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) [(0), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1) [(-3), (4), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) [(3), (3), (1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) [(-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) [(3), (-4), (3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5) [(-2), (2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) [(2), (-1), (-1), (-3), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) [(3), (-4), (-3), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) [(3), (-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) [(-1), (3), (2), (-4), (-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) [(-4), (4), (-3), (2), (4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) [(-1), (0), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) [(2), (0), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) [(4), (3), (4), (1), (2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) [(3), (-2), (2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6) [(-2), (3), (1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) [(3), (-2), (4), (4), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) [(-4), (4), (3), (3), (4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) [(-2), (-4), (3), (2), (1), (-4)])))

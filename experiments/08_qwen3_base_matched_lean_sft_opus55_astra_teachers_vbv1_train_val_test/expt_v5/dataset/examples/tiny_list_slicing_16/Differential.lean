import Mathlib
namespace Tiny
def solution (n k : Nat) (xs : List Int) : Int := ((xs.drop n).take k).sum
theorem spec_zero (k : Nat) (xs : List Int) : solution 0 k xs = (xs.take k).sum := by rfl
theorem test_window : solution 1 2 [1, 2, 3, 4] = 5 := by decide
theorem test_past_end : solution 5 2 [1, 2] = 0 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) [(4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) [(3), (4), (4), (1), (-4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) [(-1), (-3), (0), (0), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) [(4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (5) [(-2), (3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (6) [(-3), (-2), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) [(3), (2), (1), (1), (-1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) [(-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1) [(2), (3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) [(4), (-2), (1), (-3), (0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (5) [(2), (-2), (-4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) [(1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) [(-3), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) [(-3), (-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1) [(-3), (-3), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) [(3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) [(-1), (-3), (2), (4), (2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) [(2), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (5) [(-2), (4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) [(-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) [(0), (2), (1), (-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) [(0), (0), (2), (-1), (-4), (-4)])))

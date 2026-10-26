import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : List Int := xs.drop n
theorem spec_zero (xs : List Int) : solution 0 xs = xs := by rfl
theorem test_suffix : solution 2 [1, 2, 3] = [3] := by decide
theorem test_long : solution 5 [1, 2] = [] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(3), (2), (-2), (3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(1), (-4), (2), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-1), (-4), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-4), (1), (-1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-2), (-2), (3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(2), (3), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(3), (-4), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(4), (3), (2), (3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-3), (-3), (-3), (0), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-1), (-2), (-3), (-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-4), (4), (4), (-1), (-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(3), (-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3), (-1), (-3), (3), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-1), (-1), (-4)])))

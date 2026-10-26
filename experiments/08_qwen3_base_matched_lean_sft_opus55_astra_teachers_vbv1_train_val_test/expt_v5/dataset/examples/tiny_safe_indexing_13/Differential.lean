import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs.take 1
theorem spec_shape (xs : List Int) : solution xs = [] ∨ ∃ x, solution xs = [x] := by
  cases xs with
  | nil => simp [solution]
  | cons x xs => simp [solution]
theorem test_empty : solution [] = [] := by decide
theorem test_head : solution [2, 3] = [2] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-2), (-1), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (3), (-1), (4), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-1), (-4), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (0), (2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (2), (-4), (4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (4), (4), (0), (3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (0), (0), (-4), (3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (2)])))

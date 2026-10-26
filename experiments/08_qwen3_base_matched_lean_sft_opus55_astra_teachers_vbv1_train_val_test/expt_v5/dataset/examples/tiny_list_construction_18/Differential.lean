import Mathlib
namespace Tiny
def solution (xs : List Int) : List Nat := [xs.length]
theorem spec_head (xs : List Int) : (solution xs).head? = some xs.length := by simp [solution]
theorem test_empty : solution [] = [0] := by decide
theorem test_length : solution [2, -1, 4] = [3] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (0), (-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-4), (-3), (1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (2), (-1), (-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-3), (-2), (-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (1), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-4), (-3), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (3), (-3), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (0), (0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-4), (-4), (-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (2), (-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-1), (-1), (4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-2), (2), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (2), (4), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (0), (-4), (-1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (3), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))

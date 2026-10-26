import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs ++ []
theorem spec_identity (xs : List Int) : solution xs = xs := by simp [solution]
theorem test_empty : solution [] = [] := by decide
theorem test_values : solution [2, -1] = [2, -1] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (0), (-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (1), (1), (-2), (3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-2), (-2), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (0), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (0), (3), (3), (-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-2), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-1), (-4), (2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (4), (4), (-4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (2), (-3), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-1), (-2), (0), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (1), (0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (0), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (1), (-3), (4), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (1), (1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (4), (2), (1)])))

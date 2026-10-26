import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs ++ xs
theorem spec_length (xs : List Int) : (solution xs).length = xs.length + xs.length := by simp [solution]
theorem test_empty : solution [] = [] := by decide
theorem test_repeat : solution [1, -2] = [1, -2, 1, -2] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-2), (-4), (-4), (-2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-4), (-1), (4), (1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-4), (4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-3), (1), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (3), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-4), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (2), (-1), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-2), (3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-3), (-4), (-1), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-2), (-3), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-3), (1), (-4), (0), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-1)])))

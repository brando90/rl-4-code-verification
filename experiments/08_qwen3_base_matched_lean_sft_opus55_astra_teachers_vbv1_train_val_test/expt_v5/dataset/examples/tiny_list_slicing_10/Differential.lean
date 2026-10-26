import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs.drop xs.length
theorem spec_empty (xs : List Int) : solution xs = [] := by
  simp [solution]
theorem test_values : solution [1, -2, 1] = [] := by decide
theorem test_empty : solution [] = [] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-1), (4), (4), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-2), (-1), (-4), (0), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-2), (3), (-1), (-2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (1), (-4), (1), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-2), (-4), (0), (3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-1), (0), (2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (0), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (1), (4), (0), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-1), (-1), (0), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (0), (1), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-1), (3)])))

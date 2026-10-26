import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := []
theorem spec_empty (xs : List Int) : solution xs = [] := by rfl
theorem test_nonempty : solution [1, 2] = [] := by decide
theorem test_empty : solution [] = [] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-2), (4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (4), (0), (0), (-1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-3), (-3), (-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (1), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (0), (1), (3), (4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-4), (-4), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-2), (-3), (-1), (-2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (1), (-3), (1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (3), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (1), (-2), (0), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (2), (-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-2), (-3), (3), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-4), (0), (2), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-2), (0), (-3), (-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (3), (-4), (1), (4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (1), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-1), (-4), (1), (0), (1)])))

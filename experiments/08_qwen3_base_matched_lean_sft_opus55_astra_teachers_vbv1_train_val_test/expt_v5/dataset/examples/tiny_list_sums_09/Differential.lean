import Mathlib
namespace Tiny
def solution (xs : List Int) : Int := (xs.map abs).sum
theorem spec_cons (a : Int) (xs : List Int) : solution (a :: xs) = abs a + solution xs := by rfl
theorem test_empty : solution [] = 0 := by decide
theorem test_mixed : solution [3, -5, 2] = 10 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (1), (-3), (4), (-1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (2), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-4), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-3), (1), (0), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (1), (-2), (0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (1), (1), (-3), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (3), (-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (3), (1), (-3), (2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-1), (-3), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))

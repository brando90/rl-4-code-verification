import Mathlib
namespace Tiny
def solution (xs : List Int) : Int := (xs.map fun a => -a).sum
theorem spec_cons (a : Int) (xs : List Int) : solution (a :: xs) = -a + solution xs := by rfl
theorem test_empty : solution [] = 0 := by decide
theorem test_mixed : solution [3, -5, 2] = 0 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-3), (4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-1), (-3), (2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-2), (-2), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (1), (0), (-1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (1), (-4), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (4), (2), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-3), (-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (4), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-1), (0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-3), (4), (-3), (-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-1), (0), (-3), (3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (2), (-1), (-3), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (2), (1), (3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-4), (-2), (3), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (3), (2)])))

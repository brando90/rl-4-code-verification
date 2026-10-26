import Mathlib
namespace Tiny
def solution (xs : List Int) : Int := (xs.filter fun a => a < 0).sum
theorem spec_cons_negative (a : Int) (xs : List Int) (h : a < 0) : solution (a :: xs) = a + solution xs := by simp [solution, h]
theorem test_empty : solution [] = 0 := by decide
theorem test_mixed : solution [3, -5, 0, 2] = -5 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-3), (0), (2), (-4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-3), (1), (-1), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (2), (-3), (-2), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-1), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-1), (-1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (4), (2), (2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-1), (-1), (-1), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-3), (3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (4), (-1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (3), (-2), (-4), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (2), (1), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))

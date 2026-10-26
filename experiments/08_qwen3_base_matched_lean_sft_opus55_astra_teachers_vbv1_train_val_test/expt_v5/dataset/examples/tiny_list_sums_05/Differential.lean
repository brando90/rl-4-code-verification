import Mathlib
namespace Tiny
def solution (xs : List Int) : Int := xs.reverse.sum
theorem spec_reverse_invariant (xs : List Int) : solution xs = xs.sum := by simp [solution]
theorem test_empty : solution [] = 0 := by decide
theorem test_mixed : solution [3, -5, 2] = 0 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-1), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (3), (0), (2), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (2), (0), (2), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (4), (2), (2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-4), (1), (4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-4), (4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (0), (3), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (0), (2), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (1), (1), (-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-2), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (1), (-1), (-1), (-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-1), (4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1)])))

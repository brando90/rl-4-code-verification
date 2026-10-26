import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Nat := min xs.length ys.length
theorem spec_le_left (xs ys : List Int) : solution xs ys ≤ xs.length := by simp [solution]
theorem test_short_left : solution [1] [2, 3] = 1 := by decide
theorem test_empty : solution [] [2] = 0 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (3), (4), (0)] [(4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-3)] [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-4), (-3), (3)] [(2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-3), (3), (3), (0), (-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (4)] [(1), (0), (2), (-1), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (3)] [(-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (1), (3), (3), (2), (-2)] [(-3), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-4), (-2), (-1)] [(0), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-4), (-2), (4), (-4), (2)] [(1), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-2)] [(-2), (-2), (2), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2)] [(2), (1), (1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (4), (-2), (1)] [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (4)] [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-4), (-1), (0)] [(-4), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-2), (-2), (-4)] [(3), (3), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (0), (-2), (-1), (1), (4)] [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-2), (2)] [(-4), (2), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (0), (4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-3)] [(3), (2), (-2), (3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-1), (3), (1)] [(3), (1), (4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-2), (-4), (1), (1), (4)] [(2), (-1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-4)] [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-1)] [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (0), (-2), (-1), (-4)] [(1), (4), (1), (-2), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (3)] [(-1), (3), (-2), (-2), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2)] [(1), (3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (2), (-4), (-3), (-4)] [(-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (2), (-2), (-4), (1)] [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(0), (-2), (3), (4), (1), (3)])))

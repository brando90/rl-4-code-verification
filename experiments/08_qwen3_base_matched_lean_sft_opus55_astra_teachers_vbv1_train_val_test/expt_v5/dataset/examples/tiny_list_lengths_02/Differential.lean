import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Nat := (xs ++ ys).length
theorem spec_append (xs ys : List Int) : solution xs ys = xs.length + ys.length := by simp [solution]
theorem test_empty : solution [] [1] = 1 := by decide
theorem test_order : solution [2, 1] [2, 3] = 4 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-4), (2), (-2), (2), (1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (2)] [(4), (-3), (-2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1)] [(2), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-4), (-2), (0), (4), (-2)] [(-1), (-4), (3), (-3), (2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (1), (0), (3)] [(4), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (3), (-1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (3)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-2), (2), (1), (4)] [(-4), (0), (0), (-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(2), (3), (-4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3)] [(1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3)] [(-3), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (3), (3)] [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-1), (3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (0)] [(0), (4), (1), (0), (-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (0), (-1)] [(-3), (-3), (0), (-1), (2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-4), (0), (0), (1), (-3)] [(3), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-3), (-1), (2)] [(3), (0), (-4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-2), (-1)] [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4)] [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (2), (2), (4)] [(4), (1), (-1), (0), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-1), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-3), (-1), (-3), (-2), (-2)] [(-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1)] [(-4), (1), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (4), (1)] [(-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-2), (2), (1)] [(2), (3), (-2), (4), (4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (0), (4), (2)] [(-4), (3), (2), (1), (2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-3), (-2), (0), (3), (4)] [(-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-3), (-3), (-4)] [(-3), (-2), (-4), (-4)])))

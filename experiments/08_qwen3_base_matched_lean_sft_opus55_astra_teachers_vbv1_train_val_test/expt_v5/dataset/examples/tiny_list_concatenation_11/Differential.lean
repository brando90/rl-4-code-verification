import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := (xs ++ ys).reverse
theorem spec_reverse (xs ys : List Int) : solution xs ys = ys.reverse ++ xs.reverse := by simp [solution]
theorem test_empty : solution [] [1, 2] = [2, 1] := by decide
theorem test_order : solution [2, -1] [3] = [3, -1, 2] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (2)] [(-2), (-1), (-4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (4), (2), (1), (0)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-1), (4), (3)] [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (2), (-1), (1), (4), (4)] [(-1), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-4), (-4), (-4), (-1), (2)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (1)] [(3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-1)] [(-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (4), (-2), (-4)] [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-3), (1), (-4)] [(0), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-4), (-4)] [(1), (2), (-4), (3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-2), (-4)] [(-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (2), (-2), (-3)] [(-4), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (4), (-4), (0), (-4), (1)] [(-4), (0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-1), (-4), (-1), (3)] [(-2), (-1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (1)] [(-4), (-3), (3), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-3), (3), (4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(4), (0), (3), (1), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (0), (-1), (-2)] [(-2), (-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-1)] [(4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (3), (-4)] [(0), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3)] [(-3), (-2), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-4)] [(4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (3), (0), (0), (-2)] [(0), (3), (4), (-4), (-1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-2), (4), (-4), (3), (2)] [(0), (1), (-4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2)] [(2), (0), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-3), (0), (4), (-3), (1)] [(-1), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (4), (-4)] [(4), (-3), (3), (-4), (2), (3)])))

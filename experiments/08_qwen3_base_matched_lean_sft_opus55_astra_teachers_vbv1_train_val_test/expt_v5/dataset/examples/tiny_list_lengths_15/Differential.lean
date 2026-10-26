import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Bool := xs.length == ys.length
theorem spec_true_iff (xs ys : List Int) : solution xs ys = true ↔ xs.length = ys.length := by simp [solution]
theorem test_equal : solution [1, 2] [-3, 4] = true := by decide
theorem test_unequal : solution [1] [2, 3] = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (3), (2)] [(1), (0), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-1), (-1), (-3)] [(4), (3), (-2), (3), (-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (4), (3), (3), (3), (-2)] [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (4), (4), (-2), (-4), (-1)] [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (4), (-4), (1), (0), (-3)] [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-1), (-4), (1), (2), (-4)] [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-4), (0)] [(-3), (-2), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (2)] [(0), (0), (-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (2), (2), (-4)] [(0), (4), (0), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-1), (-1), (1)] [(-4), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (1), (3)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (0), (3), (2), (-4)] [(0), (0), (3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-3), (3), (1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-4)] [(-1), (0), (0), (-1), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-2), (-2)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4)] [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-2), (1), (-2)] [(-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-1), (-2)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (2), (0), (2), (-2), (-4)] [(2), (-1), (0), (4), (2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-2), (-2)] [(-4), (2), (-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (3), (3)] [(2), (-3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (4), (-2)] [(-4), (-4), (3), (3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-3), (-3), (-1), (4), (-4)] [(1), (-4), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (4), (4), (2), (3), (-1)] [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-1), (-2), (4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (1), (-1), (0), (2)] [(-4), (4), (0), (0)])))

import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Nat := (xs.toFinset \ ys.toFinset).card
theorem spec_empty_right (xs : List Int) : solution xs [] = xs.toFinset.card := by
  simp [solution]
theorem test_remove : solution [1, 2, 2, 3] [2] = 2 := by decide
theorem test_empty : solution [] [1] = 0 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-1), (-2), (2), (1), (-1)] [(3), (-1), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (2), (4), (2), (3)] [(-4), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (2), (3)] [(-2), (-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (4), (4)] [(-3), (2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-1), (2), (3), (2)] [(-4), (3), (2), (0), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-4), (-4)] [(-3), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (4), (2), (-4), (-2), (0)] [(4), (-2), (1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(2), (0), (3), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (4), (-1), (-4), (-2), (-3)] [(-1), (4), (-2), (2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (3), (0), (-4), (-3), (-2)] [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-1)] [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (2), (0), (-4)] [(0), (1), (-4), (2), (0), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (1), (2), (2)] [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(2), (0), (-2), (-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (4), (-3), (4), (-1)] [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (3)] [(-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (2), (-4), (-3), (0), (-2)] [(1), (-3), (3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-2)] [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(1), (-4), (1), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-1), (1), (-4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2)] [(-4), (3), (0), (3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-1), (1), (-2)] [(-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (3)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(3), (-1), (-3), (3), (-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-4), (-2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-2)] [(-1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-4), (-3), (-3), (3)] [(3), (1), (2), (4), (4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (2), (-2), (4), (-3), (-2)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (2), (-2), (2), (-1)] [(2), (4), (4)])))

import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Nat := xs.count x
theorem spec_matching_head (x : Int) (xs : List Int) : solution x (x :: xs) = solution x xs + 1 := by simp [solution]
theorem test_none : solution 4 [1, 2, 3] = 0 := by decide
theorem test_duplicates : solution 2 [2, 1, 2] = 2 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-4), (-1), (-3), (1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(4), (-1), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(0), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(3), (4), (1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(4), (2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-2), (4), (0), (-4), (-2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(4), (-3), (2), (-4), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(4), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(2), (2), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-2), (-1), (4), (-2), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(-4), (-4), (-3), (-2), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-4), (2), (-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(4), (-4), (0), (4), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(2), (0), (1), (-1), (-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(3), (3), (3), (-1), (2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-3), (-1), (-4), (-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(0), (2), (2), (2), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(2), (-1), (-2), (-3), (4)])))

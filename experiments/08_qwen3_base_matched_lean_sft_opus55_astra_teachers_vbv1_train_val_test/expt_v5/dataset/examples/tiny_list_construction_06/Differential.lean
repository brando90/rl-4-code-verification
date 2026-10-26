import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : List Int := xs ++ [x]
theorem spec_last (x : Int) (xs : List Int) : (solution x xs).getLast? = some x := by simp [solution]
theorem test_empty : solution 5 [] = [5] := by decide
theorem test_order : solution (-1) [2, 3] = [2, 3, -1] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-3), (-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-4), (3), (-3), (-3), (-3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(2), (4), (1), (-3), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(0), (3), (1), (-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(0), (3), (-1), (-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-3), (0), (4), (-4), (0), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-3), (-3), (4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(1), (2), (0), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(3), (4), (3), (-3), (4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(1), (-3), (4), (2), (3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-3), (2), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-4), (-4), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(3), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(2), (2), (0), (4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-2), (2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(3), (4), (-2), (-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(4), (4), (3), (-1), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-1), (-1), (-1), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-2), (-1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-1), (-2)])))

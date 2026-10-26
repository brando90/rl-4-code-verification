import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Nat := (xs ++ [x]).length
theorem spec_snoc (x : Int) (xs : List Int) : solution x xs = xs.length + 1 := by simp [solution]
theorem test_empty : solution 9 [] = 1 := by decide
theorem test_many : solution (-1) [2, 3] = 3 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(4), (-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-1), (1), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-1), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(1), (4), (-2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(3), (-4), (3), (1), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(4), (-3), (-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(-2), (4), (1), (-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(4), (-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(0), (-3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(0), (-3), (3), (1), (0), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-3), (2), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-3), (-2), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-4), (0), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(2), (4), (-1), (-1), (-4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(2), (3), (-4), (3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(1), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(2), (-4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(4), (-2), (-1), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(0), (-4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [])))

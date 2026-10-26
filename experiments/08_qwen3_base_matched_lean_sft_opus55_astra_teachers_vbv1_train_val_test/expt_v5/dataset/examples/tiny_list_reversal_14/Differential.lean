import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Nat := xs.reverse.count x
theorem spec_count (x : Int) (xs : List Int) : solution x xs = xs.count x := by simp [solution]
theorem test_empty : solution 2 [] = 0 := by decide
theorem test_count : solution 2 [1, 2, 3, 2] = 2 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-3), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-2), (-4), (-1), (-2), (4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-3), (-4), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(-1), (-2), (-1), (-2), (2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(3), (-4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(1), (2), (0), (0), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-2), (0), (-4), (4), (-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(0), (-4), (4), (0), (1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(4), (3), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(3), (2), (4), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(2), (4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-1), (4), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-1), (-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(1), (4), (1), (2), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(3), (-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(2), (-1), (-4), (1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(4), (-4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [])))

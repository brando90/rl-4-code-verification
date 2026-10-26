import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Nat := (xs.map fun a => a + x).length
theorem spec_map (x : Int) (xs : List Int) : solution x xs = xs.length := by simp [solution]
theorem test_empty : solution 4 [] = 0 := by decide
theorem test_many : solution (-2) [1, 3, 5] = 3 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(2), (-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-4), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-2), (2), (4), (-4), (-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-1), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-4), (-3), (-2), (-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3), (4), (-2), (4), (-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(4), (-3), (-1), (2), (-1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(4), (2), (2), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-1), (-2), (3), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(0), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-4), (-1), (1), (1), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(-2), (1), (4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(2), (0), (1), (-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-1), (-4), (0)])))

import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Int := (xs.map fun a => a + x).sum
theorem spec_cons (x a : Int) (xs : List Int) : solution x (a :: xs) = a + x + solution x xs := by rfl
theorem test_empty : solution 4 [] = 0 := by decide
theorem test_mixed : solution 2 [3, -5] = 2 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(0), (3), (3), (-2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-2), (4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-2), (3), (1), (2), (-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(3), (3), (1), (2), (3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(1), (2), (-4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(2), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-2), (-3), (2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-3), (4), (-4), (-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-4), (1), (1), (3), (-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-3), (3), (3), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(1), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(3), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(-3), (2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-4), (-1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-2), (1), (1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(3), (-1), (-4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(3), (0), (-1), (-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-4), (2), (3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(0), (0)])))

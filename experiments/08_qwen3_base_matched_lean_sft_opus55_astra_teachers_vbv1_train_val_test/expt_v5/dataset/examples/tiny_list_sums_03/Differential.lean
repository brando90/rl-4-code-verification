import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Int := (x :: xs).sum
theorem spec_add_head (x : Int) (xs : List Int) : solution x xs = x + xs.sum := by rfl
theorem test_empty : solution 4 [] = 4 := by decide
theorem test_mixed : solution (-2) [5, 1] = 4 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(0), (2), (4), (4), (2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(3), (0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(1), (4), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(3), (0), (3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-1), (-3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-4), (-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-2), (-1), (-3), (4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(4), (-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(3), (-3), (-1), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-3), (-2), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(0), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(2), (0), (4), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(1), (3), (-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(-1), (1), (-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(4), (-2), (0), (-1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(-2), (4), (1), (-1), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-3), (4), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(4), (-2), (3), (3), (2)])))

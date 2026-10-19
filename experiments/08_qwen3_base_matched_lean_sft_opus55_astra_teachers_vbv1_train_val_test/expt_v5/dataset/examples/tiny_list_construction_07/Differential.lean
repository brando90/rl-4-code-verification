import Mathlib
namespace Tiny
def solution (x y : Int) (xs : List Int) : List Int := x :: xs ++ [y]
theorem spec_head (x y : Int) (xs : List Int) : (solution x y xs).head? = some x := by simp [solution]
theorem test_empty : solution 1 2 [] = [1, 2] := by decide
theorem test_order : solution (-1) 4 [2, 3] = [-1, 2, 3, 4] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) [(-2), (-2), (-3), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (3) [(-3), (0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-1) [(0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (5) [(1), (2), (1), (3), (-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (4) [(-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (6) [(-2), (-1), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-2) [(1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-5) [(0), (2), (-1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-3) [(3), (1), (3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-6) [(0), (-1), (0), (2), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-1) [(3), (3), (-4), (1), (4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-3) [(-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-1) [(-2), (-1), (-3), (4), (0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-1) [(-1), (-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (1) [(-4), (4), (-3), (-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-3) [(1), (2), (-4), (-2), (4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6) [(-2), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (1) [(0), (4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (4) [(0), (-2), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-6) [(-3), (-3), (-2), (2), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-4) [(-2), (4), (-2), (-4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) [(1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-6) [(3), (4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-2) [(3), (4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1) [(2), (4), (4), (0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) [])))

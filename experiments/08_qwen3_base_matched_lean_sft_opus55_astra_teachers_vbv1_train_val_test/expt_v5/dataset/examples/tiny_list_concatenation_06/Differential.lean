import Mathlib
namespace Tiny
def solution (x : Int) (xs ys : List Int) : List Int := [x] ++ xs ++ ys
theorem spec_head (x : Int) (xs ys : List Int) : (solution x xs ys).head? = some x := by simp [solution]
theorem test_empty : solution 1 [] [] = [1] := by decide
theorem test_order : solution (-1) [2] [3, 4] = [-1, 2, 3, 4] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-3), (1), (2)] [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(3), (1), (-3)] [(-3), (0), (-4), (1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-4), (-3)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-1), (2), (4), (-3), (4), (1)] [(-2), (3), (1), (0), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(2), (-4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(3), (-4), (2)] [(2), (4), (-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3), (-2), (3), (0), (1)] [(-2), (-3), (1), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(0), (4), (3), (-1), (-2)] [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-2), (1), (2), (-1)] [(1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(0), (0), (3)] [(3), (-2), (1), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(3)] [(-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(2), (1), (-4), (1), (1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(0)] [(4), (0), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(2), (1), (-2), (3)] [(1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-2), (-2), (0), (4), (-3)] [(1), (-3), (-4), (-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(4), (4), (1), (4)] [(-1), (2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3), (2), (-1), (3), (-2)] [(-2), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-4), (-2), (-3), (2), (-3), (-3)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-3), (-3), (2)] [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(3), (-1), (-4), (-2), (-2), (-1)] [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [] [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-1), (0), (1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-1), (-1), (-4), (-3)] [(3), (-4), (0), (-2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(1), (-3)] [(4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(-3), (2)] [(2), (-3), (-1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-1), (4), (0)] [(-2), (2), (-4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(4)] [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-4), (-2), (1), (3)] [(1), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(0), (-4), (2)] [(0), (3), (-3), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(-1), (2), (-3)] [(-2)])))

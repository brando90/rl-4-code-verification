import Mathlib
namespace Tiny
def solution (n : Nat) (xs ys : List Int) : List Int := (xs ++ ys).take n
theorem spec_zero (xs ys : List Int) : solution 0 xs ys = [] := by rfl
theorem test_crosses_boundary : solution 3 [1, 2] [3, 4] = [1, 2, 3] := by decide
theorem test_long : solution 5 [1] [2] = [1, 2] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-4), (2), (0), (-3)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(4)] [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(0), (3), (2)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-1), (2), (2)] [(4), (-3), (-3), (-1), (-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(1)] [(1), (1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(2), (-4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(2), (0), (0), (-1), (-3), (-4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-4), (-3), (-4), (-1)] [(3), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-1)] [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(1)] [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(2), (3), (2)] [(-3), (-1), (4), (-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(4)] [(-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [] [(0), (-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(2), (4), (3)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(0)] [(-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(3), (3), (1)] [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-1), (0), (-4), (0)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [] [(-1), (4), (2), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-2), (0), (4), (-3), (2)] [(2), (0), (-3), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(4), (4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3), (-4), (4)] [(-1), (4), (-4), (-2), (4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-2), (4), (2), (-1), (4), (2)] [(1), (-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-4), (-2)] [(-2), (2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(2), (1), (2), (-4), (2), (3)] [(4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(4), (-2)] [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(2), (0), (-4), (2), (-3)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-2), (-4), (3), (2)] [(3), (-1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(0), (4), (4), (2), (1), (3)] [(4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(1), (-2)] [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [] [(0), (-3), (4), (-1), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-1), (-3), (2), (-4), (2), (-4)] [])))

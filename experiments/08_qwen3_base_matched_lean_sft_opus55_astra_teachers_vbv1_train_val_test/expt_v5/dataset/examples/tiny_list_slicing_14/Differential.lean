import Mathlib
namespace Tiny
def solution (n : Nat) (xs ys : List Int) : List Int := (xs ++ ys).drop n
theorem spec_zero (xs ys : List Int) : solution 0 xs ys = xs ++ ys := by rfl
theorem test_crosses_boundary : solution 3 [1, 2] [3, 4] = [4] := by decide
theorem test_long : solution 5 [1] [2] = [] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-4), (4), (2), (1), (-3), (3)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(3), (-4), (-3), (1), (-4), (4)] [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-2), (1), (-4)] [(-2), (1), (-2), (-1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-1), (2)] [(2), (-2), (2), (4), (-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(3), (-2), (-1)] [(1), (1), (0), (-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-2), (-2), (2), (0), (2)] [(-4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-4), (-2), (2), (2), (1), (4)] [(3), (0), (-1), (1), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(0)] [(4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(0), (1), (3), (3)] [(2), (2), (3), (0), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-3), (3)] [(4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(3), (0)] [(-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-3)] [(-2), (-3), (4), (4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(0), (-4), (-2), (-1), (-2)] [(1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(2), (1), (1), (-3), (-3), (4)] [(2), (-4), (-4), (2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(2), (-2), (1), (-3), (-3), (1)] [(2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-1), (0), (0), (-2)] [(-2), (0), (0), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(1), (4)] [(-3), (1), (0), (-3), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-4)] [(2), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-1), (0)] [(0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [] [(4), (1), (2), (0), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [] [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(3)] [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-3), (-4), (1), (-3)] [(4), (1), (4), (-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(1), (3), (3), (3)] [(-1), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-4), (4), (0), (3), (-3), (3)] [(-4), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(4), (1), (4)] [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [] [(-3), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-3)] [(0), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(3), (4), (-2)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [] [(-3), (-2), (-1), (-2), (-4), (-3)])))

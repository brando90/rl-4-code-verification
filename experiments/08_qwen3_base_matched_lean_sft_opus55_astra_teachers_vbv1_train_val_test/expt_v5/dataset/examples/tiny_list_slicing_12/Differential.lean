import Mathlib
namespace Tiny
def solution (n : Nat) (xs ys : List Int) : List Int := xs.drop n ++ ys
theorem spec_zero (xs ys : List Int) : solution 0 xs ys = xs ++ ys := by rfl
theorem test_suffix : solution 2 [1, 2, 3] [4] = [3, 4] := by decide
theorem test_long : solution 5 [1, 2] [3] = [3] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-1), (1), (-3), (-3)] [(2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(3), (-4)] [(-4), (-2), (3), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(0), (-3)] [(-3), (0), (3), (-3), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [] [(-2), (-4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [] [(4), (-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [] [(2), (2), (2), (-1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(2), (1), (0), (1)] [(-3), (-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [] [(-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(3), (-4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-3), (2), (-3), (3), (0)] [(1), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(1), (4), (-3), (1), (-3)] [(-1), (2), (0), (-3), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-3)] [(-2), (-1), (1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(0), (-1), (4), (4), (-1)] [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(4), (2)] [(-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-4), (0), (-2), (-2)] [(3), (2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(3), (3), (2), (-2)] [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(2), (4)] [(-2), (4), (0), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(2), (2), (2), (-4), (-1)] [(3), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-1), (1), (2), (2), (-2), (1)] [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(3), (-1), (0), (-3), (2), (4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [] [(0), (3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [] [(1), (2), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(2), (4), (-4), (1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(0)] [(-2), (-2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(1), (2), (-4), (-4)] [(1), (0), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [] [(4), (-2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(3), (-1), (-2), (4), (0)] [(-3), (1), (3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-1)] [(0), (4), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(4), (1)] [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(3)] [(4)])))

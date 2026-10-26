import Mathlib
namespace Tiny
def solution (n : Nat) (xs ys : List Int) : List Int := xs.take n ++ ys
theorem spec_zero (xs ys : List Int) : solution 0 xs ys = ys := by rfl
theorem test_prefix : solution 2 [1, 2, 3] [4] = [1, 2, 4] := by decide
theorem test_long : solution 5 [1, 2] [3] = [1, 2, 3] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-1), (0), (-1), (3), (1), (-2)] [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [] [(1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [] [(4), (3), (4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-1), (-3), (-3), (-4)] [(-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(2)] [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(3), (-1)] [(-4), (-4), (-2), (-2), (-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-2), (-4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(1)] [(-2), (-2), (-1), (0), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(1), (-4), (-1)] [(4), (-3), (-3), (1), (4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-2), (0), (4), (1)] [(1), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-1), (-1), (-3), (-2)] [(4), (-3), (-1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(3), (0), (2)] [(2), (0), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [] [(1), (1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-4), (-1), (2), (-1), (1)] [(2), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(2), (3), (-2), (3), (4), (4)] [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(3), (-2)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [] [(3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(3), (-2), (2)] [(1), (1), (4), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-4), (-4), (-1)] [(0), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(0), (-3), (1), (-4), (-1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [] [(-4), (-4), (-4), (-1), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3), (1), (-4), (-1), (4), (-2)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3), (1), (-4)] [(4), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(0), (4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(1), (3), (1), (1), (3), (-4)] [(4), (-3), (2), (-2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-2), (-2), (0), (-3), (4), (-4)] [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-3), (3)] [(-1), (3), (2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-4)] [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-1), (0), (-4)] [(-1), (2), (-4), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [] [(-3), (-1)])))

import Mathlib
namespace Tiny
def solution (x : Int) (xs ys : List Int) : Bool := (xs ++ ys).contains x
theorem spec_contains (x : Int) (xs ys : List Int) : solution x xs ys = (xs.contains x || ys.contains x) := by simp [solution]
theorem test_found : solution (-1) [2, -1] [3] = true := by decide
theorem test_missing : solution 4 [2] [-1, 3] = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(2)] [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(4), (2), (3), (-2)] [(4), (-4), (3), (3), (2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(-3), (-3), (4)] [(0), (2), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-1), (4)] [(0), (0), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(2), (-1), (3), (2), (-4), (1)] [(-2), (1), (1), (-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(0), (1), (-2)] [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(3), (-4), (0), (-4), (-1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-1), (2), (-4)] [(0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(0), (3)] [(0), (-2), (0), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-3), (-1), (0)] [(0), (0), (4), (4), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-4), (3), (1)] [(-2), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(4), (-1), (4), (-1), (3), (-3)] [(-2), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(2), (3)] [(-4), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-1)] [(0), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(2), (-1)] [(0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(4)] [(4), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(3), (4), (3), (2), (2), (1)] [(0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(-3), (4), (1)] [(-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(1), (-2)] [(1), (2), (3), (4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-3), (-4), (1), (-4), (2)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(1)] [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-4), (4), (3), (1)] [(0), (0), (-2), (1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [] [(2), (-4), (1), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [] [(-1), (-1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(0)] [(-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-4), (-2)] [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-1), (1), (3), (4), (-1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-4), (4), (-3), (-3), (-4), (2)] [(1), (4), (2), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-3)] [(1), (3), (1), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-3), (0), (-2), (3)] [(4), (0), (0)])))

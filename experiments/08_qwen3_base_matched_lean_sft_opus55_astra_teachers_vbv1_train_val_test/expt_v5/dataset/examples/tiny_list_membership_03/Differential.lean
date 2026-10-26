import Mathlib
namespace Tiny
def solution (x : Int) (xs ys : List Int) : Bool := xs.contains x || ys.contains x
theorem spec_membership (x : Int) (xs ys : List Int) : solution x xs ys = true ↔ x ∈ xs ∨ x ∈ ys := by simp [solution]
theorem test_left : solution 2 [2] [3] = true := by decide
theorem test_absent : solution 4 [1] [2, 3] = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3), (1), (4), (2)] [(-4), (-1), (2), (-2), (2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [] [(-4), (-3), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(0)] [(3), (-3), (-2), (2), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(3), (3), (4), (0), (2), (0)] [(4), (3), (2), (4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-1), (2), (0), (-3), (2), (1)] [(-4), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(3), (-1), (-2), (2), (4), (-3)] [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(4)] [(-3), (-3), (-4), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [] [(-3), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(0), (4), (1), (-2), (-1)] [(1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(2), (-3), (0), (4), (-1), (-3)] [(-3), (2), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(2), (-1), (-3), (4), (-4), (-1)] [(-2), (4), (3), (3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(-1), (-3), (-1), (-2), (2)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(3), (-4), (0), (0), (4)] [(-4), (-4), (2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-3), (2), (4), (0), (1), (2)] [(2), (3), (-4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(1), (4), (3), (-4), (2), (1)] [(-2), (-2), (-4), (-4), (0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-4), (3)] [(-3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-3), (2)] [(0), (-3), (3), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(2), (-4), (-3), (0)] [(4), (3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [] [(-1), (-4), (4), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [] [(3), (1), (-3), (-1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-4), (-1), (4), (1)] [(1), (3), (-1), (1), (-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-2), (-4)] [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(1), (-2)] [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(4), (-4), (-3), (-1), (1), (-3)] [(-2), (-1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [] [(-4), (2), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(0), (-4), (-1), (-1), (0)] [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(4)] [(-4), (-2), (4), (-1), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(2), (-3), (3), (2), (-4), (-1)] [(4), (-4), (2), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-1), (-2)] [(-1), (0), (-4), (0)])))

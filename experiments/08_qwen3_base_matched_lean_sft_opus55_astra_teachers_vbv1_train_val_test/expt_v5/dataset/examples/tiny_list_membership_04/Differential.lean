import Mathlib
namespace Tiny
def solution (x y : Int) (xs : List Int) : Bool := x == y || xs.contains x
theorem spec_membership (x y : Int) (xs : List Int) : solution x y xs = true ↔ x = y ∨ x ∈ xs := by simp [solution]
theorem test_head : solution 2 2 [3] = true := by decide
theorem test_absent : solution 4 2 [1, 3] = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) [(2), (-3), (-4), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-1) [(-2), (-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (1) [(-4), (2), (2), (1), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-1) [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) [(-3), (-2), (2), (-1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-6) [(0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-6) [(-2), (0), (1), (-2), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (5) [(-4), (-1), (4), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-2) [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1) [(0), (-4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4) [(-4), (-1), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-5) [(-2), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (3) [(4), (-2), (-3), (2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4) [(-4), (0), (4), (-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-6) [(-4), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-3) [(-1), (0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2) [(1), (-2), (1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-2) [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (5) [(0), (-1), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (6) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-5) [(4), (2), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-2) [(1), (-4), (-4), (-1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (5) [(-3), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2) [(-3), (2), (-1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (3) [(0), (-3), (-1), (4), (-1)])))

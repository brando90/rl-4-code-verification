import Mathlib
namespace Tiny
def solution (x y : Int) (xs : List Int) : Bool := xs.contains x || x == y
theorem spec_membership (x y : Int) (xs : List Int) : solution x y xs = true ↔ x ∈ xs ∨ x = y := by simp [solution]
theorem test_last : solution 2 2 [3] = true := by decide
theorem test_absent : solution 4 2 [1, 3] = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (0) [(-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-2) [(-2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-6) [(2), (4), (0), (4), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3) [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4) [(3), (0), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) [(-3), (0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-3) [(2), (-4), (-1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-3) [(0), (-1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-4) [(-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (5) [(-1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (3) [(2), (-3), (-2), (1), (3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (3) [(-2), (1), (-2), (-2), (1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-6) [(0), (1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1) [(-2), (2), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1) [(-1), (4), (-3), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (0) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-4) [(-1), (3), (0), (0), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (3) [(-4), (-2), (-4), (2), (2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3) [(2), (-1), (2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) [(2), (-4), (3), (-2), (4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (0) [])))

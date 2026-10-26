import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Bool := xs.contains x
theorem spec_membership (x : Int) (xs : List Int) : solution x xs = true ↔ x ∈ xs := by simp [solution]
theorem test_present : solution 2 [1, 2, 3] = true := by decide
theorem test_absent : solution 4 [1, 2, 3] = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-4), (-1), (1), (-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-2), (-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(4), (4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(4), (2), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(2), (0), (-3), (0), (2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(2), (3), (-1), (1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(3), (-2), (0), (1), (4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-2), (-2), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(2), (4), (-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(1), (1), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(1), (2), (-1), (-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(2), (-1), (4), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(4), (-2), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(1), (1), (-2), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(3), (-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-3), (0), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-3), (-1), (2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-1), (-1), (2), (-1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(0), (1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(0), (-4), (1), (4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3), (-4), (-1), (3), (-4)])))

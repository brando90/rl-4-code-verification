import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Bool := xs.contains x
theorem spec_any_equal (x : Int) (xs : List Int) : solution x xs = true ↔ ∃ a ∈ xs, a = x := by simp [solution]
theorem test_found : solution 2 [1, 2, 3] = true := by decide
theorem test_absent : solution 4 [1, 2, 3] = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(-3), (3), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-1), (2), (3), (4), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-3), (-4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-3), (3), (3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-3), (-1), (-4), (-1), (0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(1), (0), (-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(4), (-2), (-1), (4), (2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(4), (4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(-3), (0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-2), (4), (-3), (1), (0), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(3), (3), (0), (0), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(4), (-3), (-3), (0), (3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(-3), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(3), (-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(3), (-3), (1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(0), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(2), (2), (2), (2), (-1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(2), (0), (-4), (-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(4), (0), (3), (-3), (0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(1), (0), (3), (1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-3), (3), (-4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(4), (-4), (0), (3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(0), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(4)])))

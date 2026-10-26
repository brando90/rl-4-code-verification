import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Bool := xs.all fun a => a == x
theorem spec_all_equal (x : Int) (xs : List Int) : solution x xs = true ↔ ∀ a ∈ xs, a = x := by simp [solution]
theorem test_all_equal : solution 2 [2, 2, 2] = true := by decide
theorem test_not_all_equal : solution 2 [2, 3] = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(4), (4), (1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-4), (-1), (0), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(1), (4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-1), (-3), (3), (4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(2), (-3), (1), (-2), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-2), (3), (-1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(3), (-4), (0), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-2), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-4), (3), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(-1), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(-1), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-1), (1), (-1), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-3), (-2), (4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3), (0), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(4), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-3), (4), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-4), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-2), (0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(4), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(4), (2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-2), (-3), (4), (-3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-1), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(3), (3), (1), (-3), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-1), (0), (4), (2), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(2), (-4), (4), (1), (-2)])))

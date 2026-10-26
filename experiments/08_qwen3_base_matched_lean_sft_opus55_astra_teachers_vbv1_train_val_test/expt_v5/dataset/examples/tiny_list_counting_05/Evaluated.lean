import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Bool := decide (xs.count x ≤ xs.length)
theorem spec_always_true (x : Int) (xs : List Int) : solution x xs = true := by
  simp [solution, List.count_le_length]
theorem test_empty : solution 2 [] = true := by decide
theorem test_duplicates : solution 2 [2, 2, 1] = true := by decide
end Tiny
#print axioms Tiny.spec_always_true
#print axioms Tiny.test_empty
#print axioms Tiny.test_duplicates
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-2), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-1), (-2), (2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-1), (-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-3), (4), (3), (3), (2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-2), (0), (1), (3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(4), (-3), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(2), (2), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-1), (3), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(2), (-1), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(1), (1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-4), (-2), (3), (4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-4), (2), (-2), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(2), (3), (-2), (4), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-1), (-3), (1), (-1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-2), (3), (-1), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(0), (1), (-2), (3), (0), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-4), (1), (3), (-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(4), (-1), (3), (3), (4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(2), (-4), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(4), (0), (-3), (1), (-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-1)])))

import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Nat := xs.reverse.count x
theorem spec_preserved (x : Int) (xs : List Int) : solution x xs = xs.count x := by simp [solution]
theorem test_duplicates : solution 2 [2, 1, 2] = 2 := by decide
theorem test_empty : solution 2 [] = 0 := by decide
end Tiny
#print axioms Tiny.spec_preserved
#print axioms Tiny.test_duplicates
#print axioms Tiny.test_empty
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-2), (1), (4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(2), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-1), (3), (0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(0), (0), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-1), (-3), (4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(2), (2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(0), (-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(0), (-3), (2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(1), (-3), (4), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(1), (3), (-1), (-4), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(4), (-4), (-4), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-1), (-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(0), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(2), (1), (-1), (3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-4), (-2), (0), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(1), (-1), (-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [])))

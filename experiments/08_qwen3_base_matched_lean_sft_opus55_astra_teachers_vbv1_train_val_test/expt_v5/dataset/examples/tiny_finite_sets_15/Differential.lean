import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Nat := (xs ++ [x]).toFinset.card
theorem spec_empty (x : Int) : solution x [] = 1 := by
  simp [solution]
theorem test_present : solution 2 [1, 2, 2] = 2 := by decide
theorem test_new : solution 3 [1, 2] = 3 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(1), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-4), (3), (1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(1), (0), (-4), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-1), (2), (0), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(2), (0), (1), (-1), (0), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-4), (4), (2), (0), (4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-2), (3), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3), (-2), (2), (-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(4), (-4), (2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(0), (3), (-4), (-4), (1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(2), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(2), (2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-4), (0), (-1), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-2), (4), (-2), (-1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(4), (-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(2), (-3), (2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-4), (3), (-4), (1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(3), (-4), (3), (4), (-3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(4), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(4), (0), (1), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-1), (0), (-2), (2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(0), (2), (-3), (-2), (-1)])))

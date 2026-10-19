import Mathlib
namespace Tiny
def solution (y : Int) (n : Nat) (xs : List Int) : Int := xs.getD n 0 + y
theorem spec_empty (y : Int) (n : Nat) : solution y n [] = y := by simp [solution]
theorem test_index : solution 5 1 [2, 3] = 8 := by decide
theorem test_default : solution 5 2 [2] = 5 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) [(-3), (-4), (2), (-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) [(-1), (-4), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6) [(2), (2), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6) [(-3), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) [(4), (-3), (-1), (-4), (-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) [(3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (3) [(1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (5) [(3), (-2), (-2), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (2) [(-2), (-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) [(-1), (1), (4), (0), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) [(-1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) [(2), (4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (2) [(-3), (-2), (2), (1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) [(0), (-4), (-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (0) [(-1), (1), (-4), (1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4) [(4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) [(4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (5) [(0), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (5) [(1), (-1), (3), (-4), (-2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) [(-3), (3), (4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4) [(-2), (-2), (-1), (-3), (-1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) [(0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) [(0), (0), (4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (4) [(-4), (-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (5) [])))

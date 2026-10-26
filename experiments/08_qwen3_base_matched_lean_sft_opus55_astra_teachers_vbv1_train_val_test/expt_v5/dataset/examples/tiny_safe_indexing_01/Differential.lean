import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs : List Int) : Int := xs.getD n x
theorem spec_zero (x a : Int) (xs : List Int) : solution x 0 (a :: xs) = a := by rfl
theorem test_index : solution 9 1 [2, 3] = 3 := by decide
theorem test_default : solution 9 2 [2] = 9 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (4) [(-1), (-4), (-4), (-1), (-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (4) [(4), (1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) [(1), (-2), (4), (-3), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) [(2), (3), (-2), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4) [(-1), (4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) [(4), (-1), (-3), (1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (3) [(4), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) [(-2), (0), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) [(4), (1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1) [(-2), (0), (-1), (-1), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) [(-3), (0), (1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1) [(-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (5) [(-1), (-2), (0), (2), (4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (1) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) [(-1), (4), (-1), (4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) [(-2), (2), (0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4) [(0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (6) [(2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (0) [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) [(-1), (-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) [(3), (2), (-3), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) [(2), (-2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4) [(2), (-4), (4), (3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2) [(0), (0), (-3), (-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) [(-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) [(2), (2), (2), (-1), (-4)])))

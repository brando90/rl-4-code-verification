import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Int := xs.getD 1 x
theorem spec_pair (x a b : Int) (xs : List Int) : solution x (a :: b :: xs) = b := by rfl
theorem test_second : solution 9 [2, 3] = 3 := by decide
theorem test_default : solution 9 [2] = 9 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(-2), (-3), (-2), (-2), (2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-1), (-2), (1), (-3), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(4), (0), (-1), (2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(2), (1), (3), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(1), (-3), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-1), (1), (1), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(1), (-2), (2), (1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(3), (3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(1), (4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(0), (-3), (0), (0), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(2), (-1), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(1), (0), (4), (-1), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(3), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(4), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(1), (3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(3), (1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(4), (3), (1), (4), (-1)])))

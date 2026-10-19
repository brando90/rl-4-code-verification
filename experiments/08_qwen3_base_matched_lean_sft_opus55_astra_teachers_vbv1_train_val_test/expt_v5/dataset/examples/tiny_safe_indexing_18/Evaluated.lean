import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs : List Int) : Int := xs.reverse.getD n x
theorem spec_empty (x : Int) (n : Nat) : solution x n [] = x := by rfl
theorem test_reversed : solution 9 1 [2, 3, 4] = 3 := by decide
theorem test_default : solution 9 2 [2] = 9 := by decide
end Tiny
#print axioms Tiny.spec_empty
#print axioms Tiny.test_reversed
#print axioms Tiny.test_default
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4) [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) [(0), (-4), (3), (4), (-1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) [(4), (0), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6) [(-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) [(1), (0), (2), (-2), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (4) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) [(1), (-3), (0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3) [(-2), (-4), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1) [(1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6) [(2), (2), (-3), (4), (4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (6) [(-1), (1), (-4), (-4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4) [(2), (2), (-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) [(2), (2), (-4), (-1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (5) [(-3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (1) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) [(0), (4), (2), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (5) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4) [(-4), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) [(-2), (3), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) [(1), (-4), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) [(-3), (-3), (0), (4), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4) [(4), (2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1) [(1), (2), (-2), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) [(2), (2), (-1), (1), (-4)])))

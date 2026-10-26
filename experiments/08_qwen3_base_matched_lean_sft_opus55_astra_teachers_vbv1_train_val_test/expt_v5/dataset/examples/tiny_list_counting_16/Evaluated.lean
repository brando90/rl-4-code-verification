import Mathlib
namespace Tiny
def solution (x y : Int) (xs : List Int) : Nat := xs.count x
theorem spec_append (x y : Int) (xs zs : List Int) :
    solution x y (xs ++ zs) = solution x y xs + solution x y zs := by simp [solution]
theorem test_shifted : solution 2 (-3) [2, 1, 2] = 2 := by decide
theorem test_empty : solution 2 5 [] = 0 := by decide
end Tiny
#print axioms Tiny.spec_append
#print axioms Tiny.test_shifted
#print axioms Tiny.test_empty
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) [(2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-5) [(4), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) [(-1), (-4), (-4), (0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) [(2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) [(-4), (-2), (0), (-4), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-5) [(-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-2) [(-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (3) [(-1), (-3), (-2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-5) [(-2), (2), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4) [(3), (3), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-5) [(3), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-6) [(2), (-2), (4), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-1) [(1), (2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (2) [(0), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-2) [(2), (-1), (-3), (3), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-6) [(-2), (-4), (-4), (-4), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) [(3), (-1), (1), (0), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-6) [(3), (2), (0), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (4) [(2), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-2) [(4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) [(3), (-2), (1), (-2)])))

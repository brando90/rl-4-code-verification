import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs ys : List Int) : Int := (xs ++ ys).getD n x
theorem spec_empty (x : Int) (n : Nat) : solution x n [] [] = x := by rfl
theorem test_left : solution 9 1 [2, 3] [4] = 3 := by decide
theorem test_right : solution 9 2 [2] [3, 4] = 4 := by decide
end Tiny
#print axioms Tiny.spec_empty
#print axioms Tiny.test_left
#print axioms Tiny.test_right
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) [(3), (2), (2), (2), (4), (2)] [(0), (2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) [(1), (-4)] [(-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) [] [(0), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2) [(-2), (-2), (-1)] [(3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) [(2), (4), (-1), (3), (4), (-2)] [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) [(-4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (1) [] [(-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) [(0), (2)] [(-1), (0), (-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (5) [(1), (-1), (-1), (-1)] [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) [(4), (2), (-2), (-2), (1)] [(2), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) [(1), (3), (-1), (1), (1)] [(4), (2), (-4), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) [(0), (2), (-3), (-1), (-2), (0)] [(1), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (5) [(2), (2)] [(-2), (3), (1), (-1), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) [(-2), (-3), (1), (0)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4) [(3), (0)] [(-2), (2), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (5) [(-4), (-2), (1)] [(-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1) [(-4), (4), (1)] [(1), (-2), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) [] [(-2), (-3), (0), (-3), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (1) [(4), (3)] [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (5) [(-4), (-2), (2), (-3), (4), (1)] [(1), (-3), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2) [(-4), (-3), (-4), (0), (4), (-2)] [(-2), (-2), (1), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) [(3), (0), (-4), (0), (3)] [(3), (4), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) [(-4), (-2), (1), (-1), (0)] [(2), (-3), (1), (0), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3) [] [(-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (5) [(-1), (1), (4), (3), (-4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (0) [] [(3), (1), (-2), (-3), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5) [] [(3), (0), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) [(-4), (-3), (2), (-1), (-1), (3)] [(-3), (-4), (-2), (2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) [(4), (-2), (-1), (-3)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) [(3)] [])))

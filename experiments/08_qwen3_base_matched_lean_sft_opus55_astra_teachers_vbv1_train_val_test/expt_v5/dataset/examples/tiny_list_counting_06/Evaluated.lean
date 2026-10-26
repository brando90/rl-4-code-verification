import Mathlib
namespace Tiny
def solution (x : Int) (xs ys : List Int) : Nat := (xs ++ ys).count x
theorem spec_split (x : Int) (xs ys : List Int) :
    solution x xs ys = xs.count x + ys.count x := by simp [solution]
theorem test_both : solution 2 [2, 1] [2, 2] = 3 := by decide
theorem test_empty : solution 1 [] [2] = 0 := by decide
end Tiny
#print axioms Tiny.spec_split
#print axioms Tiny.test_both
#print axioms Tiny.test_empty
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-1), (4), (-2), (-3), (-1)] [(3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(3)] [(1), (-3), (-3), (2), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [] [(4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-3), (2)] [(0), (-2), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-4)] [(-2), (3), (-1), (3), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [] [(1), (-3), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(1), (-4)] [(-4), (-3), (1), (1), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(0), (-3), (-2), (4)] [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [] [(4), (3), (-2), (0), (-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-3), (0), (-3), (1)] [(3), (1), (4), (-2), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(3), (-2)] [(-4), (-3), (-2), (-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(1), (1), (-4), (1), (-3), (3)] [(2), (3), (3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [] [(4), (3), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(0)] [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3), (4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(0), (1), (-4)] [(2), (4), (2), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [] [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(4), (0), (-2), (3), (2), (-2)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(3), (0)] [(0), (-2), (-4), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [] [(0), (4), (-2), (-1), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-1), (-1), (2), (0), (-2), (-4)] [(3), (-4), (-1), (0), (1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(3), (-4), (4), (1), (1), (4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-3), (3), (-4), (-2)] [(-3), (-4), (4), (-1), (-1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-4), (-3), (-2), (4), (-2), (-4)] [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(0)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(0), (3), (-3), (3), (0), (2)] [(4), (3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-1), (1), (1), (-1), (0), (4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(0), (2), (-1), (1), (1), (0)] [(3), (4), (-1), (-4), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(0), (1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-3), (4), (-3), (-1)] [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-1), (-2), (-2), (0), (-1)] [(-3), (1), (0)])))

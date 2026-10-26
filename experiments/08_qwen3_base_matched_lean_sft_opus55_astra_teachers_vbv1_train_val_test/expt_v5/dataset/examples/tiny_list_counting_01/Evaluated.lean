import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Nat := xs.count x
theorem spec_append (x : Int) (xs ys : List Int) :
    solution x (xs ++ ys) = solution x xs + solution x ys := by simp [solution]
theorem test_duplicates : solution 2 [2, 1, 2] = 2 := by decide
theorem test_absent : solution 4 [2, 1, 2] = 0 := by decide
end Tiny
#print axioms Tiny.spec_append
#print axioms Tiny.test_duplicates
#print axioms Tiny.test_absent
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(1), (-4), (-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-3), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(1), (-4), (-2), (4), (-1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-4), (-3), (-2), (0), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(1), (-3), (4), (-4), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-1), (1), (4), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-1), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(4), (-1), (3), (-1), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(-4), (1), (-4), (0), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-1), (-4), (-2), (1), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-4), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(2), (1), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-1), (1), (0), (4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-4), (-1), (-2), (-1), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-1), (-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(-3), (-1), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(4), (3), (1), (-4), (3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-3), (0), (-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [])))

import Mathlib
namespace Tiny
def solution (x y : Int) (xs : List Int) : Nat := xs.count x + xs.count y
theorem spec_symmetric (x y : Int) (xs : List Int) : solution x y xs = solution y x xs := by
  simp [solution, Nat.add_comm]
theorem test_distinct : solution 1 2 [1, 2, 1] = 3 := by decide
theorem test_equal : solution 2 2 [2, 1, 2] = 4 := by decide
end Tiny
#print axioms Tiny.spec_symmetric
#print axioms Tiny.test_distinct
#print axioms Tiny.test_equal
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) [(-3), (2), (-3), (4), (4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2) [(2), (-4), (-1), (3), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1) [(-4), (3), (4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (1) [(-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-5) [(-1), (0), (-1), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2) [(3), (-1), (1), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6) [(-4), (2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-5) [(-4), (4), (-2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-2) [(-4), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1) [(-1), (-2), (0), (-2), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-5) [(-4), (-1), (4), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-5) [(3), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-1) [(-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (6) [(2), (3), (2), (2), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-1) [(-1), (0), (-1), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1) [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) [(-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-3) [(-2), (2), (-1), (4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) [(1), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) [(-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-3) [(1), (2), (-3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-2) [(0), (-3), (0), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) [(-2), (0), (-1), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-3) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-6) [(2), (1), (-1), (1), (3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (3) [(-2), (-4), (-4), (4), (-1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-6) [(-2), (-2), (-2), (-4), (1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) [(3), (0), (1), (4)])))

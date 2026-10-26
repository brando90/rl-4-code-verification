import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs : List Int) : Nat := (xs.take n).count x + (xs.drop n).count x
theorem spec_total (x : Int) (n : Nat) (xs : List Int) : solution x n xs = xs.count x := by
  rw [solution, ← List.count_append, xs.take_append_drop]
theorem test_middle : solution 2 2 [2, 1, 2, 2] = 3 := by decide
theorem test_past_end : solution 2 9 [2, 1] = 1 := by decide
end Tiny
#print axioms Tiny.spec_total
#print axioms Tiny.test_middle
#print axioms Tiny.test_past_end
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (2) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) [(-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) [(-4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (3) [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (6) [(3), (1), (-2), (4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (1) [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (0) [(2), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) [(2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (2) [(-4), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (4) [(1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6) [(3), (-4), (-3), (2), (-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (0) [(1), (-2), (2), (1), (2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (1) [(-1), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4) [(-2), (4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) [(4), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2) [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6) [(-1), (1), (-3), (3), (3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) [(4), (2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) [(3), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) [(2), (3), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (1) [(-4), (-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) [(1), (2), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) [(-3), (4), (4), (0), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (4) [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4) [(4), (3), (0), (-2), (0), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) [(2), (0), (4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) [(-2), (4), (-4), (2), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) [(0), (4), (2), (-1), (-1)])))

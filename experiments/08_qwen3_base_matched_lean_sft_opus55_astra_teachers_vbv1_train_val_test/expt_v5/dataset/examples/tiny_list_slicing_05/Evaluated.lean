import Mathlib
namespace Tiny
def solution (n k : Nat) (xs : List Int) : List Int := (xs.take n).take k
theorem spec_zero (k : Nat) (xs : List Int) : solution 0 k xs = [] := by
  simp [solution]
theorem test_shorter_second : solution 3 2 [1, 2, 3, 4] = [1, 2] := by decide
theorem test_shorter_first : solution 1 5 [1, 2, 3] = [1] := by decide
end Tiny
#print axioms Tiny.spec_zero
#print axioms Tiny.test_shorter_second
#print axioms Tiny.test_shorter_first
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4) [(-1), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4) [(0), (3), (-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) [(0), (0), (-4), (-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (6) [(4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) [(1), (-1), (1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6) [(1), (1), (-2), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (5) [(1), (-2), (-2), (1), (4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) [(0), (3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) [(-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) [(1), (-2), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) [(-1), (-4), (4), (-1), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (6) [(1), (-3), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) [(-2), (4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4) [(4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) [(0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) [(0), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) [(-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (3) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4) [(-3), (-3), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) [(-4), (-4), (-4), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) [(-4), (-2), (1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (3) [(-4), (2), (3), (1), (2), (0)])))

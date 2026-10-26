import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : Bool := xs.take n == xs
theorem spec_zero (xs : List Int) : solution 0 xs = (xs == []) := by
  cases xs <;> rfl
theorem test_enough : solution 3 [1, 2] = true := by decide
theorem test_short : solution 1 [1, 2] = false := by decide
end Tiny
#print axioms Tiny.spec_zero
#print axioms Tiny.test_enough
#print axioms Tiny.test_short
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(3), (-2), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(1), (3), (-1), (-4), (2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-3), (4), (4), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(3), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(1), (2), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-2), (2), (1), (0), (1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(3), (0), (2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(4), (3), (-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-2), (0), (-4), (4), (-2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(0), (-4), (4), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(0), (-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(1), (-2), (-4), (2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(3), (-4), (-3), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(4), (3), (-3), (0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-4), (2), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(2), (-3)])))

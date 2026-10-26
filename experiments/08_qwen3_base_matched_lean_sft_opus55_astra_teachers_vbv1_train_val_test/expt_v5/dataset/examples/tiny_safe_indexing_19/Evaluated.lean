import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : List Int := (xs.drop n).take 1
theorem spec_zero (xs : List Int) : solution 0 xs = xs.take 1 := by rfl
theorem test_index : solution 1 [2, 3] = [3] := by decide
theorem test_missing : solution 2 [2] = [] := by decide
end Tiny
#print axioms Tiny.spec_zero
#print axioms Tiny.test_index
#print axioms Tiny.test_missing
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(2), (4), (-1), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(0), (-3), (-1), (-2), (-3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(4), (-2), (1), (4), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(4), (0), (0), (-4), (-1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-3), (-1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(1), (0), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-1), (3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-4), (-2), (2), (0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-1), (2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(0), (1), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-4), (-1), (-2), (-4), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(0), (-3), (4), (3), (-1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(0), (-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(3), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(1), (2), (3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-2), (4), (2), (0), (-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(2), (3), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(1), (-2), (-3), (2), (3)])))

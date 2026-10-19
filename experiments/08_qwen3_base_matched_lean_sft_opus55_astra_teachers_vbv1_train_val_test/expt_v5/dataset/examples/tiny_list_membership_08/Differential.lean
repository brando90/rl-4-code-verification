import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs : List Int) : Bool := (xs.drop n).contains x
theorem spec_suffix (x : Int) (n : Nat) (xs : List Int) : solution x n xs = true ↔ x ∈ xs.drop n := by simp [solution]
theorem test_before_suffix : solution 1 1 [1, 2, 3] = false := by decide
theorem test_in_suffix : solution 3 1 [1, 2, 3] = true := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) [(-2), (2), (-1), (0), (-1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2) [(-3), (-4), (1), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (3) [(-2), (3), (-4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2) [(-1), (0), (-2), (-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) [(-1), (-1), (-4), (1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) [(-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) [(1), (-3), (-2), (-2), (-2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) [(-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (5) [(-4), (-1), (1), (0), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) [(2), (0), (2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) [(-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (2) [(-1), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) [(-2), (2), (-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (5) [(-4), (-3), (-2), (0), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) [(0), (-1), (-4), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (1) [(-2), (-3), (-1), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) [(0), (2), (-2), (4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (0) [(2), (2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) [(3), (3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) [(-3), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (6) [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) [(-3), (-3), (-4), (0), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (5) [])))

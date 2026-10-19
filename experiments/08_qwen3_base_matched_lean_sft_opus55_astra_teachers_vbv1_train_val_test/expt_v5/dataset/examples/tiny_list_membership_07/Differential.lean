import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs : List Int) : Bool := (xs.take n).contains x
theorem spec_prefix (x : Int) (n : Nat) (xs : List Int) : solution x n xs = true ↔ x ∈ xs.take n := by simp [solution]
theorem test_in_prefix : solution 2 2 [1, 2, 3] = true := by decide
theorem test_after_prefix : solution 3 2 [1, 2, 3] = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) [(2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (6) [(-2), (0), (-1), (-1), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2) [(-4), (3), (-1), (2), (-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4) [(3), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) [(0), (-2), (2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (3) [(0), (1), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (1) [(2), (0), (-1), (2), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (1) [(-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (5) [(-1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2) [(4), (-2), (0), (-3), (3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) [(2), (3), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (1) [(-2), (0), (0), (-3), (4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) [(4), (-4), (-4), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (3) [(3), (-4), (-2), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (3) [(3), (4), (4), (-2), (3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (3) [(-1), (2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) [(-4), (0), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (0) [(0), (-3), (-1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (1) [(3), (0), (-4), (3), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (1) [(1), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (0) [(0), (3), (-2), (3), (4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (6) [(4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (0) [(0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2) [(3), (-3), (4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) [(-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (6) [(0), (-4), (-3), (-3), (-4), (1)])))

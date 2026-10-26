import Mathlib
namespace Tiny
def solution (x y : Int) (xs : List Int) : Bool := xs.any fun a => a + y == x
theorem spec_shifted (x y : Int) (xs : List Int) : solution x y xs = true ↔ ∃ a ∈ xs, a + y = x := by simp [solution]
theorem test_found : solution 5 2 [1, 3, 4] = true := by decide
theorem test_absent : solution 6 2 [1, 3] = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5) [(1), (0), (-1), (0), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (5) [(-4), (-3), (-1), (-3), (3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) [(-1), (3), (-4), (4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-3) [(-2), (3), (3), (3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (2) [(-2), (3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-1) [(0), (-2), (-4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (1) [(2), (-3), (-2), (-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3) [(0), (4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-2) [(4), (-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) [(4), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-6) [(2), (3), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-1) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-5) [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4) [(2), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0) [(1), (1), (-2), (-1), (3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-2) [(2), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (0) [(1), (-3), (4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-3) [(1), (2), (1), (-3), (2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-4) [(-4), (-4), (0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) [(-2), (3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-5) [(3), (-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4) [(-2), (4), (0), (1), (-1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-4) [(-1), (2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) [(-2), (-2), (2), (4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (0) [(-2), (4), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1) [(-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (5) [(2), (-2), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (3) [(4), (4)])))

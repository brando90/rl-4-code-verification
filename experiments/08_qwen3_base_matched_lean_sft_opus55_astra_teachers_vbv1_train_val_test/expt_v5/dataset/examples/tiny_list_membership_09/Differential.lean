import Mathlib
namespace Tiny
def solution (xs : List Int) : Bool := xs.all fun a => 0 <= a
theorem spec_nonnegative (xs : List Int) : solution xs = true ↔ ∀ a ∈ xs, 0 ≤ a := by simp [solution]
theorem test_all_nonnegative : solution [0, 2, 5] = true := by decide
theorem test_negative : solution [0, -2, 5] = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-1), (-2), (0), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (0), (-3), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-2), (-4), (-3), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (3), (-2), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (1), (3), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (1), (2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-4), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (1), (2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (2), (1), (4), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (4), (2), (0), (-1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (0), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (3), (2), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-1), (2), (3), (2)])))

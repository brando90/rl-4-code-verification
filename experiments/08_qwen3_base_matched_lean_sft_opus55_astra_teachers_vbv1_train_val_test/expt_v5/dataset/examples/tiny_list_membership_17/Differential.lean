import Mathlib
namespace Tiny
def solution (xs : List Int) : Bool := xs.all fun a => a % 2 == 0
theorem spec_even (xs : List Int) : solution xs = true ↔ ∀ a ∈ xs, a % 2 = 0 := by simp [solution]
theorem test_all_even : solution [-2, 0, 4] = true := by decide
theorem test_odd : solution [2, 3, 4] = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (1), (2), (2), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (0), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (0), (-2), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-2), (2), (-3), (2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-4), (-1), (1), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (3), (-4), (0), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (4), (-3), (-4), (4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-3), (2), (1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-4), (-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-1), (4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (1), (-3), (-4), (0), (2)])))

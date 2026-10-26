import Mathlib
namespace Tiny
def solution (xs : List Int) : Bool := xs.sum % 2 == 0
theorem spec_cons (x : Int) (xs : List Int) : solution (x :: xs) = ((x + xs.sum) % 2 == 0) := by rfl
theorem test_empty : solution [] = true := by decide
theorem test_odd_sum : solution [1, -2, 4] = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-4), (-4), (-1), (-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (2), (3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (1), (-4), (4), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (4), (4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-2), (-3), (-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (0), (3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (4), (2), (-4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-4), (-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-4), (-4), (1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (0), (-3), (4), (2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-3), (-4), (3), (-1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-4), (4), (-1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (0), (-3), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (4), (-1), (-2), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (0), (3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2)])))

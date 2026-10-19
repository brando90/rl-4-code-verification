import Mathlib
namespace Tiny
def solution (xs : List Int) (p : Bool) : List Int := xs.filter fun _ => p
theorem spec_true (xs : List Int) : solution xs true = xs := by simp [solution]
theorem spec_false (xs : List Int) : solution xs false = [] := by simp [solution]
theorem test_true : solution [1, -2] true = [1, -2] := by decide
theorem test_false : solution [1, -2] false = [] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (2), (4), (4), (-2)] false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-2), (0), (-2)] false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0)] true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (1), (1)] false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-1), (1), (3)] false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (2), (-4), (0), (-1), (-2)] false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-1), (3), (2), (1)] true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-1), (-4), (0), (3)] true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (3), (0), (3)] false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-1), (0), (3)] true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (1), (0), (-4)] false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (2), (-2), (-1), (2)] true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-4), (-2), (-2), (0), (-3)] true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (0), (-4), (4), (-2)] true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-3), (3), (-1), (4)] true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3)] false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-3), (1), (-2), (0), (2)] true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-2), (-2), (2), (1), (-3)] true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (1)] false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (2), (-3)] true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-2), (-4), (-1), (1)] false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (4), (-2), (-1)] false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2)] false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (1), (-4), (1), (-3), (-2)] false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (2), (1), (4)] true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-2), (0), (1), (2)] true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-1), (-4), (-1), (-2)] true)))

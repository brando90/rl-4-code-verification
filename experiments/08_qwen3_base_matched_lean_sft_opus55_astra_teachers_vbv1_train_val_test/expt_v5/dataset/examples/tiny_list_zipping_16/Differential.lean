import Mathlib
namespace Tiny
def solution (xs : List Int) : List (Int × Int) := xs.zip xs
theorem spec_cons (a : Int) (xs : List Int) : solution (a :: xs) = (a, a) :: solution xs := rfl
theorem test_pairs : solution [1, -2] = [(1, 1), (-2, -2)] := by decide
theorem test_empty : solution [] = [] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-4), (-3), (2), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (1), (2), (-1), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (0), (-2), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-3), (-3), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (1), (1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-4), (-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-2), (-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-4), (-2), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-1), (4), (0), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-1), (1), (-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (0), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (1), (-4), (2), (3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (4), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (0), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-1), (2), (2)])))

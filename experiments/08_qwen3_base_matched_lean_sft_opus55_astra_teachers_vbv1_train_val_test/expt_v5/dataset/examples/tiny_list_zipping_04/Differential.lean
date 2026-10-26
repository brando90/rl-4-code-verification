import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := (xs.zip ys).map fun p => p.1 * p.2
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = (a * b) :: solution xs ys := rfl
theorem test_product : solution [2, -2] [3, 4] = [6, -8] := by decide
theorem test_truncates : solution [2, 5] [3] = [6] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1)] [(-2), (3), (-3), (1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-2), (0), (1), (3)] [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-4), (1)] [(0), (-4), (-2), (0), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-3)] [(-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (0)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-1), (-2), (-1), (1)] [(-4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1)] [(-4), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0)] [(0), (3), (-2), (1), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-3), (-1), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-4), (2)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-4), (-1), (-1), (-2), (0)] [(0), (3), (-2), (3), (2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-4), (-4), (-1)] [(2), (-1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-4), (3), (0), (4)] [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (4), (0)] [(4), (0), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-1), (2), (-2), (1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (0), (-2), (-3)] [(-3), (0), (-4), (3), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (2)] [(2), (-1), (0), (-3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (2), (-1), (1), (0), (1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2)] [(2), (3), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2)] [(-3), (-3), (0), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(3), (2), (-4), (4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (4), (2), (0)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-2), (-2), (-2), (-1), (3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-1), (3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(1), (4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (1), (0)] [(4), (0), (3), (-3), (4), (3)])))

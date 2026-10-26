import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := (xs.zip ys).map Prod.snd
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = b :: solution xs ys := rfl
theorem test_rights : solution [1] [3, 4] = [3] := by decide
theorem test_empty : solution [1] [] = [] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (0)] [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2)] [(-3), (2), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3)] [(3), (4), (-3), (-4), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-2), (-4), (2), (-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-3), (4)] [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-3), (4), (3), (-3)] [(4), (3), (-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-4), (-2), (-3), (-1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (0)] [(-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-3), (-1), (4)] [(0), (3), (3), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-4), (2), (-1), (1), (-2)] [(2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (1), (0), (-3)] [(-1), (3), (-1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1)] [(2), (-1), (-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2)] [(1), (-2), (-4), (-3), (-2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (0), (-4)] [(-2), (-4), (0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-4), (4), (1)] [(1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-1), (1), (1)] [(4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-3), (-3), (0), (-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (0), (-1), (3), (4), (4)] [(0), (3), (-3), (3), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (1), (0), (3), (1)] [(2), (4), (2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2)] [(1), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (2), (-3), (2)] [(1), (-3), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-3), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(0), (-4), (2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (4), (1), (3)] [(4), (-3), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-2), (-1)] [(3), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (4), (-2)] [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-2), (1), (3), (-1), (-4)] [(3), (-2), (1), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-3), (1)] [(-4), (0), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4)] [(0), (-2)])))

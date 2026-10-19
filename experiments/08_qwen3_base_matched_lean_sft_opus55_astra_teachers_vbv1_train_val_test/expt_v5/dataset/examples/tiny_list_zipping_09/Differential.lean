import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := (xs.zip ys).map Prod.fst
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = a :: solution xs ys := rfl
theorem test_lefts : solution [1, 2] [3] = [1] := by decide
theorem test_empty : solution [] [3] = [] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1)] [(2), (1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (0), (-1)] [(2), (4), (4), (-4), (-3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (0), (-4), (-4), (1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (3), (3), (-1)] [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-3)] [(3), (-4), (1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-1)] [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (4)] [(-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-3)] [(-1), (-1), (1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4)] [(3), (3), (-3), (0), (2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-3), (-1), (4), (-2), (-1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (3)] [(1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-3)] [(2), (0), (4), (1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (4), (4), (3), (2)] [(-4), (4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1)] [(3), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (0)] [(-1), (-2), (-1), (1), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-4), (-2), (0), (-2)] [(1), (3), (0), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-1), (1), (0), (4)] [(3), (-4), (-4), (-3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-4), (0)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (1), (2), (-4), (1), (-1)] [(-4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (3)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-1), (4)] [(2), (4), (3), (-4), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-3), (4)] [(-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-3)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-4)] [(-1), (2), (-1), (-4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (2), (-3), (-2), (-4), (0)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (3)] [(-4), (-2), (2), (-1), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-4), (-3), (3), (-3), (-4)] [(4), (-2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-3), (0), (0), (3), (4)] [(3), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (3), (-3), (2), (0), (3)] [(-3), (0), (-2), (4), (-1)])))

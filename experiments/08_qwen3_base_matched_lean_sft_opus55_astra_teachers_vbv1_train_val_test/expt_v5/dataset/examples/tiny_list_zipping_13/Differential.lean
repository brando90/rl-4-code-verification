import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Int := ((xs.zip ys).map fun p => p.1 + p.2).sum
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = a + b + solution xs ys := rfl
theorem test_sum : solution [1, -2] [3, 4] = 6 := by decide
theorem test_empty : solution [] [3] = 0 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (1), (-3)] [(0), (3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (3), (-3), (1), (-4)] [(1), (0), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-2)] [(4), (-2), (-1), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (3)] [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (0), (-3), (-1)] [(3), (2), (-1), (-3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-4)] [(-4), (1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-4), (-1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-2)] [(3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (4), (4), (2)] [(-1), (3), (0), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-3), (4), (1)] [(0), (-3), (-2), (-4), (-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (0), (4), (1), (0)] [(-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (0), (-2)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (1), (3), (3), (-2)] [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (-2)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-3), (-2), (-2), (-3), (1)] [(-3), (-3), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-3), (4), (4)] [(3), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (2), (4), (4), (2), (-4)] [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-2), (1), (4)] [(2), (-2), (4), (-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2)] [(0), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-3), (2)] [(-4), (2), (3), (4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(4), (-2), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-2), (0)] [(2), (2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-2), (-4), (-2), (-3)] [(2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3)] [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (4), (2), (2)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0)] [(3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (2)] [(0), (-1), (3), (2)])))

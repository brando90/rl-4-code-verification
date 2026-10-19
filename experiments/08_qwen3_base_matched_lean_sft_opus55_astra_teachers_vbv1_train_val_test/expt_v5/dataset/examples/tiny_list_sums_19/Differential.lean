import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Int := (List.zipWith (fun a b => a - b) xs ys).sum
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = a - b + solution xs ys := by rfl
theorem test_empty : solution [] [1, 2] = 0 := by decide
theorem test_truncate : solution [3, -5, 2] [4, 1] = -7 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (0), (1), (4), (4)] [(-3), (0), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (1)] [(-3), (3), (-1), (-1), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (3), (-4), (2)] [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-1), (-4), (-4), (2)] [(2), (-3), (4), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-3), (4), (-4), (-3), (2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (1), (-3), (-1), (4), (3)] [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-1), (-1)] [(-2), (-1), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (3), (-4), (1), (-3), (0)] [(-4), (0), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(0), (4), (2), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-2), (-3), (4)] [(-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-4), (4)] [(-4), (2), (-2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (0), (-3), (-4)] [(2), (4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-3), (4), (-4)] [(-1), (-2), (-1), (-3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-3), (4), (1), (3), (4)] [(2), (-3), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (-2), (3)] [(-4), (1), (0), (-3), (0), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-2), (-2)] [(-1), (-3), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (1), (2), (4), (-1), (3)] [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-4)] [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-1), (0), (3), (0), (4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-2), (-3)] [(-4), (4), (4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-2), (-1), (0), (2)] [(-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(2), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-1)] [(4), (0), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (2), (4)] [(2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (2), (1), (-4), (2)] [(-3), (-3), (0), (-2), (4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1)] [(-1), (2), (-3), (3), (-1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (4)] [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (-3), (-2)] [(2), (2), (1), (0), (-4), (1)])))

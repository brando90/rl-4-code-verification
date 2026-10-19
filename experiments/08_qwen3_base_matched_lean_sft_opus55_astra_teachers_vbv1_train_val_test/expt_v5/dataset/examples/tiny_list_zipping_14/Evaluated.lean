import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Bool := (xs.zip ys).all fun p => p.1 == p.2
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = ((a == b) && solution xs ys) := rfl
theorem test_all_equal : solution [1, -2] [1, -2, 3] = true := by decide
theorem test_difference : solution [1, 2] [1, 3] = false := by decide
end Tiny
#print axioms Tiny.spec_cons
#print axioms Tiny.test_all_equal
#print axioms Tiny.test_difference
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-2), (-4), (3), (3), (-3)] [(-4), (-2), (-4), (2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-3), (-4)] [(0), (0), (-2), (3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-3), (0), (1), (0), (1)] [(4), (4), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (1), (1)] [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-1), (0), (-1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (3), (0), (-2)] [(4), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (4), (-1), (2), (3)] [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (3), (0), (-2), (1)] [(-2), (4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(2), (4), (4), (3), (-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (-3)] [(4), (4), (1), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0)] [(-3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (1), (0), (0)] [(-4), (-1), (-3), (0), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (0), (1), (1)] [(4), (-3), (4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-3), (1)] [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(4), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (2), (1), (-1), (2)] [(2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (-1), (3)] [(-3), (1), (3), (3), (-2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3)] [(0), (4), (-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-3)] [(-4), (4), (-4), (-4), (-1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (4), (-4)] [(3), (-4), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-1), (4), (1), (1)] [(1), (2), (4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (3), (-4)] [(4), (1), (0), (-4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-4), (-4), (1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-1), (2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (3), (-3), (-2), (3), (0)] [(1), (-4), (0), (4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0)] [(1), (-1), (4), (-4), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (0)] [(1), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (0), (-4), (-3)] [(-4), (0), (0), (4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2)] [(-3), (-2), (-2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (1), (-4), (2), (1), (4)] [(1), (3), (-3), (-4)])))

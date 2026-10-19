import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Bool := (xs ++ ys).all fun a => decide (a >= 0)
theorem spec_empty_right (xs : List Int) : solution xs [] = xs.all (fun a => decide (a >= 0)) := by simp [solution]
theorem test_nonnegative : solution [0, 2] [3] = true := by decide
theorem test_negative : solution [0, -1] [3] = false := by decide
end Tiny
#print axioms Tiny.spec_empty_right
#print axioms Tiny.test_nonnegative
#print axioms Tiny.test_negative
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (4), (4), (-1), (-4)] [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (2), (-4), (-2), (1), (-1)] [(0), (1), (-2), (-4), (3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (-2), (0), (-1)] [(0), (3), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4), (3), (3)] [(-3), (-3), (2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (4), (2)] [(3), (-1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (4), (2), (3), (3), (-1)] [(1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (1), (4), (3), (-2), (-2)] [(1), (-3), (1), (0), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(4)] [(1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (1), (4), (2)] [(4), (1), (3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (-4), (-3), (-3), (-2), (-2)] [(3), (-4), (-1), (-3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (4), (-2), (-2), (-2), (2)] [(-2), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0)] [(1), (-4), (1), (-4), (-2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (3)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-4), (2), (1)] [(-2), (-3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3), (3)] [(-1), (-2), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-2), (-3), (-4), (3)] [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (3), (2), (2), (-2), (2)] [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1)] [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (2), (0), (-4), (-1), (1)] [(-2), (1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (0), (-1)] [(-3), (-4), (2), (4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-2), (1), (4)] [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (1), (-1), (2)] [(-1), (-1), (-1), (0), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(0), (-3)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3)] [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-1), (-3), (4), (4), (-2)] [(-4), (-4), (4), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(2), (3), (4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(-3), (0)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(3)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [] [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution [(1), (0), (-1), (1), (1)] [])))

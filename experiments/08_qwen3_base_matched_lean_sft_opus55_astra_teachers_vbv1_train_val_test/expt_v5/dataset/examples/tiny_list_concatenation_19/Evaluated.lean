import Mathlib
namespace Tiny
def solution (x : Int) (xs ys : List Int) : Bool := (xs ++ ys).any fun a => a == x
theorem spec_empty_right (x : Int) (xs : List Int) : solution x xs [] = xs.any (fun a => a == x) := by simp [solution]
theorem test_found : solution (-1) [2] [-1, 3] = true := by decide
theorem test_missing : solution 4 [2] [-1, 3] = false := by decide
end Tiny
#print axioms Tiny.spec_empty_right
#print axioms Tiny.test_found
#print axioms Tiny.test_missing
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(2), (3), (0), (2)] [(0), (-2), (-1), (2), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3)] [(0), (1), (1), (2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(3), (-4), (-2), (-4), (-3)] [(-2), (1), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(1)] [(2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(1)] [(-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [] [(-2), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-3), (3), (4)] [(-4), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(4), (-2), (1), (-1), (0), (4)] [(1), (0), (-4), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-3), (-1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3), (-2), (1), (-4), (3), (2)] [(3), (0), (2), (1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(3), (2), (0), (-3)] [(1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(0), (-1), (-2), (0), (-2)] [(-1), (-2), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(3), (4), (2), (-1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-1), (-3), (-4), (-2), (-4)] [(3), (-2), (-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(4)] [(4), (0), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-3)] [(0), (-2), (-1), (4), (-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(3), (-3), (-4), (-1)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-1), (-2), (-4), (-4)] [(4), (2), (0), (3), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-4), (0)] [(-1), (3), (-2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-2), (0), (4)] [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(4)] [(3), (-2), (-3), (0), (-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [] [(3), (-1), (4), (2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(2), (-3)] [(4), (2), (4), (4), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-3), (-2), (0), (1), (-1), (-4)] [(3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(4), (-3), (0)] [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(3), (-3)] [(-4), (2), (1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(3), (0), (-1)] [(3), (0), (2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-3), (-4), (3), (3), (0), (4)] [(-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-4), (-1), (-3), (0), (-2)] [(-2), (3), (-3), (-2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-3), (-1)] [(0), (3), (1), (-4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(4)] [(-3), (-1), (-1), (2), (-3), (-1)])))

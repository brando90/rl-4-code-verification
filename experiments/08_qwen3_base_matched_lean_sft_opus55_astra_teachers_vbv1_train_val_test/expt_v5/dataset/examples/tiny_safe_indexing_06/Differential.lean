import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Int := (xs ++ [x]).headD x
theorem spec_empty (x : Int) : solution x [] = x := by rfl
theorem test_head : solution 9 [2, 3] = 2 := by decide
theorem test_append_default : solution 9 [] = 9 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(4), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-4), (0), (1), (-2), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(0), (-4), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-4), (-2), (2), (4), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-1), (3), (3), (4), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(0), (-3), (-1), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-3), (3), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(2), (-2), (3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(1), (-3), (3), (-2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-2), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-2), (-4), (-3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(0), (-4), (1), (4), (0), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(1), (0), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(3), (-4), (2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(2), (-1), (3), (-2), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(4), (0), (2), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-3), (-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) [(-1), (0)])))

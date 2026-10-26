import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Int := ([x] ++ xs).getLastD x
theorem spec_empty (x : Int) : solution x [] = x := by rfl
theorem test_last : solution 9 [2, 3] = 3 := by decide
theorem test_default : solution 9 [] = 9 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-3), (-3), (3), (3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(-4), (1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(2), (-1), (3), (1), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(1), (-4), (4), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) [(-2), (-3), (2), (-4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(3), (-4), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-4), (4), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) [(-3), (0), (2), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(0), (-3), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(-2), (-3), (0), (-1), (3), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-2), (-3), (-2), (0), (3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(1), (0), (-4), (4), (2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(-4), (4), (1), (4), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) [(2), (4), (2), (-3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) [(4), (0), (4), (4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(-3), (-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) [(-2), (-2), (-3), (-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) [(4), (-3), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) [(2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) [(-1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) [(-2), (1), (1), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) [(1), (-4), (-2)])))

import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs : List Int) : Int := (xs.take n).getLastD x
theorem spec_zero (x : Int) (xs : List Int) : solution x 0 xs = x := by rfl
theorem test_prefix_last : solution 9 2 [2, 3, 4] = 3 := by decide
theorem test_default : solution 9 0 [2, 3] = 9 := by decide
end Tiny
#print axioms Tiny.spec_zero
#print axioms Tiny.test_prefix_last
#print axioms Tiny.test_default
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (5) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (6) [(4), (-1), (-3), (-4), (-4), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6) [(0), (3), (4), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6) [(-4), (-2), (4), (2), (2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (2) [(-1), (0), (0), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1) [(3), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (4) [(4), (2), (-1), (2), (-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) [(0), (-1), (-4), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (1) [(-1), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (3) [(3), (4), (3), (-3), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (3) [(-3), (-1), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5) [(-1), (-2), (4), (-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (6) [(-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (3) [(-1), (4), (4), (2), (1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) [(-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) [(1), (4), (1), (-2), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (5) [(4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (5) [(0), (-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (5) [(-1), (0), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (1) [(0), (4), (-1), (-2), (0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3) [(-1), (3), (-2), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2) [(-2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) [(4), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) [(0), (-1), (4), (-3), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (0) [(-3), (-4), (0), (-2), (-1), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (5) [(3), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (4) [(0), (-2), (-1), (-3), (3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (0) [])))

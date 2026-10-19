import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs : List Int) : Bool :=
  match xs.get? n with
  | some y => y == x
  | none => false
theorem spec_empty (x : Int) (n : Nat) : solution x n [] = false := by rfl
theorem test_match : solution 3 1 [2, 3] = true := by decide
theorem test_missing : solution 3 2 [2] = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (6) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) [(-2), (-2), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (3) [(-4), (-3), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (3) [(0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (1) [(-2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) [(-2), (-2), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) [(2), (-2), (-2), (-2), (1), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (0) [(2), (2), (-4), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (0) [(-4), (2), (-3), (0), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (3) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) [(0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4) [(2), (-3), (-4), (0), (2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (1) [(1), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) [(-1), (-3), (2), (3), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (3) [(4), (4), (3), (4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4) [(3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) [(-2), (-1), (-2), (2), (-1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4) [(1), (-4), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) [(0), (0), (0), (3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6) [(-3), (2), (-4), (-4), (-1), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) [(2), (-2), (-3)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) [(3), (2), (-4), (2), (0), (1)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (4) [(2), (-3), (0)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) [(2), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) [])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) [(2)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (5) [(-4), (4), (-4), (-4)])))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) [(3), (3), (1)])))

import Mathlib
namespace Tiny
def solution (x y : Int) : Nat → List Int
  | 0 => []
  | n + 1 => x :: y :: solution x y n
theorem spec_succ (x y : Int) (n : Nat) : solution x y (n + 1) = x :: y :: solution x y n := by rfl
theorem test_zero : solution 1 2 0 = [] := by decide
theorem test_repeat : solution (-1) 3 2 = [-1, 3, -1, 3] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (0) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (1) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-6) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (6) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (0) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-2) (2))))

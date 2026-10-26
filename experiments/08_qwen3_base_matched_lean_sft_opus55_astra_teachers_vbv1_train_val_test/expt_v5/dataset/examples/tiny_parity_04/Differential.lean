import Mathlib
namespace Tiny
def solution (x y : Int) : Bool := (x + y) % 2 != 0
theorem spec_commutative (x y : Int) : solution x y = solution y x := by simp [solution, add_comm]
theorem test_odd_sum : solution 2 3 = true := by decide
theorem test_even_sum : solution (-3) 1 = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-5))))

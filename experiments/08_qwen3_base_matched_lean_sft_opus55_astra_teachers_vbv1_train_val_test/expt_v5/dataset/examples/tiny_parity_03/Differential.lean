import Mathlib
namespace Tiny
def solution (x y : Int) : Bool := (x + y) % 2 == 0
theorem spec_commutative (x y : Int) : solution x y = solution y x := by simp [solution, add_comm]
theorem test_even_sum : solution 2 4 = true := by decide
theorem test_odd_sum : solution (-3) 2 = false := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2))))

import Mathlib
namespace Tiny
def solution (x y z : Int) : Int := (x + y + z) % 2
theorem spec_swap_ends (x y z : Int) : solution x y z = solution z y x := by
  simp [solution, add_comm, add_left_comm]
theorem test_even_sum : solution 1 2 3 = 0 := by decide
theorem test_odd_sum : solution (-2) 4 5 = 1 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-5) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-5) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-4) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (0) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (3) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (-4) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (5) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-4) (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-1) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-2) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-2) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-3) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2) (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (0) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-3) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (3) (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (5) (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-1) (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-5) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4) (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-2) (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (2) (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (0) (-2))))

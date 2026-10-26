import Mathlib
namespace Tiny
def solution (x : Int) : Int := x % 5
theorem spec_multiple (x : Int) : solution (5 * x) = 0 := by simp [solution]
theorem test_negative : solution (-7) = 3 := by norm_num [solution]
theorem test_positive : solution 11 = 1 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0))))

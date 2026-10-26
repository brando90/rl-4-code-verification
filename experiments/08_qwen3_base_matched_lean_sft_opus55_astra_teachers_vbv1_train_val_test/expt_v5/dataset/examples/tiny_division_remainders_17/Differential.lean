import Mathlib
namespace Tiny
def solution (x : Int) : Int := (2 * x) / 2
theorem spec_identity (x : Int) : solution x = x := by simp [solution]
theorem test_negative : solution (-7) = -7 := by norm_num [solution]
theorem test_positive : solution 8 = 8 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3))))

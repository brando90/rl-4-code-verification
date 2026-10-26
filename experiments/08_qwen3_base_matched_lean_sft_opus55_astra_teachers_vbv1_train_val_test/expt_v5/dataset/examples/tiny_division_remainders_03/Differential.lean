import Mathlib
namespace Tiny
def solution (x : Int) : Int := x / 3
theorem spec_triple (x : Int) : solution (3 * x) = x := by simp [solution]
theorem test_negative : solution (-7) = -3 := by norm_num [solution]
theorem test_positive : solution 8 = 2 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4))))

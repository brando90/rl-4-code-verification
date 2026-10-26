import Mathlib
namespace Tiny
def solution (x : Int) : Int := if x < 0 then 0 else x
theorem spec_nonnegative (x : Int) : 0 <= solution x := by
  by_cases h : x < 0 <;> simp [solution, h] <;> omega
theorem test_negative : solution (-3) = 0 := by decide
theorem test_nonnegative : solution 3 = 3 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6))))

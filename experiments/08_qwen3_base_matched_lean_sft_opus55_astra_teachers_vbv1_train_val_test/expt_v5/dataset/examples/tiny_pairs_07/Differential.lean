import Mathlib
namespace Tiny
def solution (pair : Int × Int) : Int := pair.1 - pair.2
theorem spec_self (x : Int) : solution (x, x) = 0 := by simp [solution]
theorem test_positive : solution (5, 3) = 2 := by norm_num [solution]
theorem test_negative : solution (-2, 4) = -6 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-2), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (0)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-3), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((0), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((4), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-1), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((0), (-4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((4), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (-4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((1), (-3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-2), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((4), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((4), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((0), (0)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-3), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-1), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-2), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((1), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((3), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((0), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-3), (-3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-1), (-3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((3), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-2), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-1), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((3), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-3), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (-4)))))

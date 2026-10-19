import Mathlib
namespace Tiny
def solution (pair : Int × Int) : Bool := pair.1 <= pair.2
theorem spec_reflexive (x : Int) : solution (x, x) = true := by simp [solution]
theorem test_true : solution (-2, 4) = true := by norm_num [solution]
theorem test_false : solution (5, 3) = false := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-1), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-2), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-3), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((3), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((3), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-1), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((1), (-4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((0), (0)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-2), (-4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((1), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-1), (-3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-3), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-3), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-3), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((4), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (-4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((1), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((4), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (-4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((3), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((1), (-4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-2), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-2), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((3), (-4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((0), (0)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((0), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((3), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((4), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (-2)))))

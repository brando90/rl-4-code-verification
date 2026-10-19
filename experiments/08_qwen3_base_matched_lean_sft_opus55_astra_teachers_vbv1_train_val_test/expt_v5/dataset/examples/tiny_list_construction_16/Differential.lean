import Mathlib
namespace Tiny
def solution (pair : Int × Int) : List Int := [pair.1, pair.2]
theorem spec_head (pair : Int × Int) : (solution pair).head? = some pair.1 := by simp [solution]
theorem test_positive : solution (2, 3) = [2, 3] := by decide
theorem test_negative : solution (-1, 0) = [-1, 0] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-1), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-3), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((4), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((4), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-1), (0)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (-3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((3), (-3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-3), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-1), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-1), (-4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((0), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((1), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-2), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-2), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-1), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-1), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-3), (-4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-3), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((1), (0)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((4), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-3), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((1), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((3), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-3), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-1), (0)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((3), (0)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((1), (3)))))

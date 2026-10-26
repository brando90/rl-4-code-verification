import Mathlib
namespace Tiny
def solution (pair : Int × Int) : Int := pair.1 * pair.2
theorem spec_commutative (pair : Int × Int) : solution (pair.2, pair.1) = solution pair := by
  simp [solution, mul_comm]
theorem test_positive : solution (2, 3) = 6 := by norm_num [solution]
theorem test_negative : solution (-2, 4) = -8 := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-1), (-4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-2), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((0), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((1), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((4), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (0)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-3), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-3), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((0), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((0), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((0), (-4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((1), (-3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (-3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((4), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((4), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((3), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((1), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((4), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((1), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((3), (-4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((3), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((4), (4)))))

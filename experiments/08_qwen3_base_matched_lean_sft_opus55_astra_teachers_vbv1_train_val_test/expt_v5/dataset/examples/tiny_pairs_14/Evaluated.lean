import Mathlib
namespace Tiny
def solution (x : Int) (pair : Int × Int) : Int × Int := (pair.1 + x, pair.2 + x)
theorem spec_difference (x : Int) (pair : Int × Int) : (solution x pair).1 - (solution x pair).2 = pair.1 - pair.2 := by
  simp [solution]
theorem test_positive : solution 2 (3, 4) = (5, 6) := by norm_num [solution]
theorem test_negative : solution (-2) (-3, 4) = (-5, 2) := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_difference
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) ((-2), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) ((2), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) ((-1), (0)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) ((2), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) ((-4), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) ((1), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) ((-2), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) ((-2), (-3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) ((1), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) ((-2), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) ((2), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) ((1), (-3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) ((4), (-3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) ((1), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) ((-1), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) ((4), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) ((-2), (-3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) ((4), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) ((1), (0)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) ((-3), (-3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) ((0), (-3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) ((-3), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) ((-1), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) ((3), (0)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) ((3), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) ((3), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) ((0), (-4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) ((0), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) ((0), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) ((3), (-3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) ((-1), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) ((-3), (-3)))))

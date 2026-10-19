import Mathlib
namespace Tiny
def solution (pair : Int × Int) : Int × Int := (pair.2, pair.1)
theorem spec_swap_twice (pair : Int × Int) : solution (solution pair) = pair := by
  rcases pair with ⟨x, y⟩
  rfl
theorem test_positive : solution (2, 3) = (3, 2) := by norm_num [solution]
theorem test_negative : solution (-2, 4) = (4, -2) := by norm_num [solution]
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-3), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((3), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((1), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-2), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((1), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-3), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (-4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((1), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-2), (-3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((0), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((3), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((0), (-4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((3), (3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-1), (-4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((0), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-2), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (0)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-2), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-4), (2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-2), (1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((2), (-3)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-1), (-1)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((1), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-2), (4)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((-2), (-2)))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution ((4), (-1)))))

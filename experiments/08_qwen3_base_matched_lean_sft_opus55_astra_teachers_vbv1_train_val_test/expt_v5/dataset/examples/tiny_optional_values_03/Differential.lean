import Mathlib
namespace Tiny
def solution (x : Int) (opt : Option Int) : Int := opt.getD x
theorem spec_none (x : Int) : solution x none = x := by rfl
theorem spec_some (x value : Int) : solution x (some value) = value := by rfl
theorem test_default : solution 4 none = 4 := by decide
theorem test_value : solution 4 (some (-2)) = -2 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (some (-1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (some (4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (some (2) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (some (3) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (some (1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (some (4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (some (1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (some (-4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (some (1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (some (-1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (some (3) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (some (-3) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (some (0) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (some (3) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (some (-4) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (some (2) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (some (-2) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (some (-1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (some (3) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (some (1) : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (none : Option Int))))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (some (3) : Option Int))))

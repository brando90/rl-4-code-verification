import Mathlib
namespace Tiny
def solution (x y : Int) (p q : Bool) : Int := if p || q then x else y
theorem spec_left_true (x y : Int) (q : Bool) : solution x y true q = x := by
  cases q <;> rfl
theorem test_both_false : solution 4 9 false false = 9 := by decide
theorem test_right_true : solution 4 9 false true = 4 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-3) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (0) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-6) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-3) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-4) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (3) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (6) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (0) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-5) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (1) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-6) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (2) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (2) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-5) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-2) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (-6) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-5) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (2) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (4) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (0) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (2) true false)))

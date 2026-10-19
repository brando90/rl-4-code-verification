import Mathlib
namespace Tiny
def solution (x y : Int) (p q : Bool) : Int := if p && q then x else y
theorem spec_both_true (x y : Int) : solution x y true true = x := by rfl
theorem test_both_true : solution 4 9 true true = 4 := by decide
theorem test_one_false : solution 4 9 true false = 9 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (2) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (3) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-5) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (6) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-1) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (-6) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-3) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (6) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-4) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (0) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-2) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (2) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (5) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-6) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (1) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (6) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (1) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (4) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (5) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (-3) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-3) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (6) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (5) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-3) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (2) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (5) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (6) false false)))

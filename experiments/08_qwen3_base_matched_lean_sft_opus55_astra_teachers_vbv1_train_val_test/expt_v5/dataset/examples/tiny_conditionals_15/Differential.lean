import Mathlib
namespace Tiny
def solution (x y z : Int) (p q : Bool) : Int := if p then x else if q then y else z
theorem spec_first (x y z : Int) (q : Bool) : solution x y z true q = x := by rfl
theorem test_first : solution 1 2 3 true false = 1 := by decide
theorem test_last : solution 1 2 3 false false = 3 := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (0) (6) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-1) (2) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (-3) (6) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (4) (-2) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) (-1) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-3) (-1) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) (3) (-4) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (0) (2) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (4) (3) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-2) (0) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (-2) (6) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (4) (0) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) (-1) (1) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (3) (3) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-5) (5) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (1) (5) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-4) (6) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (-5) (-6) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (3) (5) (6) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-4) (-5) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) (-5) (-3) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) (6) (-2) true true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (1) (5) (-3) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) (4) (0) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (2) (-5) true false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-3) (-1) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) (-3) (1) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) (-1) (5) false true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) (3) (2) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) (-3) (-2) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) (4) (-4) false false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) (-4) (-6) true false)))

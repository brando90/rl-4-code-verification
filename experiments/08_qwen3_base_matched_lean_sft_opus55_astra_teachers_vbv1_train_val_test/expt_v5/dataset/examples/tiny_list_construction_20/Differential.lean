import Mathlib
namespace Tiny
def solution (x : Int) (p : Bool) : List Int := if p then [x] else []
theorem spec_membership (x z : Int) (p : Bool) : z ∈ solution x p ↔ p = true ∧ z = x := by
  cases p <;> simp [solution]
theorem test_true : solution (-2) true = [-2] := by decide
theorem test_false : solution 3 false = [] := by decide
end Tiny
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-3) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-4) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-1) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-6) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (2) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (5) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-5) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (0) false)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (6) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (4) true)))
#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution (-2) true)))

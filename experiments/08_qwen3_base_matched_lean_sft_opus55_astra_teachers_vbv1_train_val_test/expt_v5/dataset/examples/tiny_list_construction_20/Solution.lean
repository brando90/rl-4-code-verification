import Mathlib
namespace Tiny
def solution (x : Int) (p : Bool) : List Int := if p then [x] else []
theorem spec_membership (x z : Int) (p : Bool) : z ∈ solution x p ↔ p = true ∧ z = x := by
  cases p <;> simp [solution]
theorem test_true : solution (-2) true = [-2] := by decide
theorem test_false : solution 3 false = [] := by decide
end Tiny

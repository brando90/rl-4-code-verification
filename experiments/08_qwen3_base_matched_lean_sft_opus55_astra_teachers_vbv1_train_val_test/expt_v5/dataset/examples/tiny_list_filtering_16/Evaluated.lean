import Mathlib
namespace Tiny
def solution (x y : Int) (xs : List Int) : List Int := xs.filter fun a => decide (a < x ∨ a > y)
theorem spec_members (a x y : Int) (xs : List Int) : a ∈ solution x y xs ↔ a ∈ xs ∧ (a < x ∨ a > y) := by simp [solution]
theorem test_outside : solution (-1) 2 [-2, -1, 0, 2, 3] = [-2, 3] := by decide
theorem test_reversed : solution 3 1 [0, 2, 4] = [0, 2, 4] := by decide
end Tiny
#print axioms Tiny.spec_members
#print axioms Tiny.test_outside
#print axioms Tiny.test_reversed

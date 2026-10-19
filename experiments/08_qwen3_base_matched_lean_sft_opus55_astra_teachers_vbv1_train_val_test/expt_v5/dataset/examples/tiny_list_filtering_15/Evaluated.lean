import Mathlib
namespace Tiny
def solution (x y : Int) (xs : List Int) : List Int := xs.filter fun a => decide (x <= a ∧ a <= y)
theorem spec_members (a x y : Int) (xs : List Int) : a ∈ solution x y xs ↔ a ∈ xs ∧ x <= a ∧ a <= y := by simp [solution, and_assoc]
theorem test_range : solution (-1) 2 [-2, -1, 0, 2, 3] = [-1, 0, 2] := by decide
theorem test_reversed : solution 3 1 [0, 2, 4] = [] := by decide
end Tiny
#print axioms Tiny.spec_members
#print axioms Tiny.test_range
#print axioms Tiny.test_reversed

import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : List Int := xs.filter fun a => decide (a != x)
theorem spec_members (a x : Int) (xs : List Int) : a ∈ solution x xs ↔ a ∈ xs ∧ a != x := by simp [solution]
theorem test_duplicates : solution 2 [2, 1, 2, -2] = [1, -2] := by decide
theorem test_empty : solution 4 [] = [] := by decide
end Tiny
#print axioms Tiny.spec_members
#print axioms Tiny.test_duplicates
#print axioms Tiny.test_empty

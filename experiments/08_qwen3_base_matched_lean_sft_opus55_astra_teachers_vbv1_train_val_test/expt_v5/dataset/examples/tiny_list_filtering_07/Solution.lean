import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : List Int := xs.filter fun a => decide (a = x)
theorem spec_members (a x : Int) (xs : List Int) : a ∈ solution x xs ↔ a ∈ xs ∧ a = x := by simp [solution]
theorem test_duplicates : solution 2 [2, 1, 2, -2] = [2, 2] := by decide
theorem test_absent : solution 4 [1, 2] = [] := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Nat := (xs.filter fun a => a != x).length
theorem spec_matching_head (x : Int) (xs : List Int) : solution x (x :: xs) = solution x xs := by simp [solution]
theorem test_none : solution 4 [1, 2, 3] = 3 := by decide
theorem test_duplicates : solution 2 [2, 1, 2] = 1 := by decide
end Tiny
#print axioms Tiny.spec_matching_head
#print axioms Tiny.test_none
#print axioms Tiny.test_duplicates

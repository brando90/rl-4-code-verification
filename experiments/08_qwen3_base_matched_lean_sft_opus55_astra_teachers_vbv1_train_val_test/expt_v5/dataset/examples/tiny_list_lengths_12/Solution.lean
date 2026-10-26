import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Nat := xs.count x
theorem spec_matching_head (x : Int) (xs : List Int) : solution x (x :: xs) = solution x xs + 1 := by simp [solution]
theorem test_none : solution 4 [1, 2, 3] = 0 := by decide
theorem test_duplicates : solution 2 [2, 1, 2] = 2 := by decide
end Tiny

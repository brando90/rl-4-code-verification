import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Nat := xs.reverse.count x
theorem spec_preserved (x : Int) (xs : List Int) : solution x xs = xs.count x := by simp [solution]
theorem test_duplicates : solution 2 [2, 1, 2] = 2 := by decide
theorem test_empty : solution 2 [] = 0 := by decide
end Tiny

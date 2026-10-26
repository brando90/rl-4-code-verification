import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Nat := (x :: xs).count x
theorem spec_increment (x : Int) (xs : List Int) : solution x xs = xs.count x + 1 := by simp [solution]
theorem test_empty : solution 2 [] = 1 := by decide
theorem test_duplicates : solution 2 [2, 1] = 2 := by decide
end Tiny

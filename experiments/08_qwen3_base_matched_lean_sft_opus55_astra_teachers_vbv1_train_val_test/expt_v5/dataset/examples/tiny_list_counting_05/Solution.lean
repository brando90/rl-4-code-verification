import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Bool := decide (xs.count x ≤ xs.length)
theorem spec_always_true (x : Int) (xs : List Int) : solution x xs = true := by
  simp [solution, List.count_le_length]
theorem test_empty : solution 2 [] = true := by decide
theorem test_duplicates : solution 2 [2, 2, 1] = true := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Nat := (xs ++ [x]).toFinset.card
theorem spec_empty (x : Int) : solution x [] = 1 := by
  simp [solution]
theorem test_present : solution 2 [1, 2, 2] = 2 := by decide
theorem test_new : solution 3 [1, 2] = 3 := by decide
end Tiny

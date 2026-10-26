import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Nat := xs.length - xs.count x
theorem spec_bound (x : Int) (xs : List Int) : solution x xs ≤ xs.length := by
  exact Nat.sub_le _ _
theorem test_duplicates : solution 2 [2, 1, 2] = 1 := by decide
theorem test_absent : solution 4 [2, 1, 2] = 3 := by decide
end Tiny

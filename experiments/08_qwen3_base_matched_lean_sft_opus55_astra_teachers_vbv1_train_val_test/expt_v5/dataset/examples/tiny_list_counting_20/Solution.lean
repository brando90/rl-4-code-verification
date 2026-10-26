import Mathlib
namespace Tiny
def solution (x y : Int) (xs : List Int) : Nat := xs.count x + xs.count y
theorem spec_symmetric (x y : Int) (xs : List Int) : solution x y xs = solution y x xs := by
  simp [solution, Nat.add_comm]
theorem test_distinct : solution 1 2 [1, 2, 1] = 3 := by decide
theorem test_equal : solution 2 2 [2, 1, 2] = 4 := by decide
end Tiny

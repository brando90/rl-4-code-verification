import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Nat := (xs.toFinset ∩ ys.toFinset).card
theorem spec_commutative (xs ys : List Int) : solution xs ys = solution ys xs := by
  simp [solution, Finset.inter_comm]
theorem test_overlap : solution [1, 2, 2] [2, 3] = 1 := by decide
theorem test_empty : solution [] [1] = 0 := by decide
end Tiny

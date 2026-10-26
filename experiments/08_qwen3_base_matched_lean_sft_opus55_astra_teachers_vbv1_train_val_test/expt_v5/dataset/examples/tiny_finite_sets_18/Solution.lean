import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Bool := decide (xs.toFinset ∩ ys.toFinset = ys.toFinset ∩ xs.toFinset)
theorem spec_commutative (xs ys : List Int) : solution xs ys = true := by
  simp [solution, Finset.inter_comm]
theorem test_empty : solution [] [1] = true := by decide
theorem test_overlap : solution [1, 2] [2, 3] = true := by decide
end Tiny

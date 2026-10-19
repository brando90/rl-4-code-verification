import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Bool := decide (xs.toFinset ⊆ xs.toFinset ∪ ys.toFinset)
theorem spec_superset (xs ys : List Int) : solution xs ys = true := by
  simp [solution]
theorem test_empty : solution [] [1] = true := by decide
theorem test_overlap : solution [1, 2] [2, 3] = true := by decide
end Tiny

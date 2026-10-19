import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Bool := decide (Disjoint (xs.toFinset \ ys.toFinset) ys.toFinset)
theorem spec_disjoint (xs ys : List Int) : solution xs ys = true := by
  simp [solution, Finset.disjoint_left]
theorem test_overlap : solution [1, 2] [2, 3] = true := by decide
theorem test_equal : solution [1, 2] [1, 2] = true := by decide
end Tiny
#print axioms Tiny.spec_disjoint
#print axioms Tiny.test_overlap
#print axioms Tiny.test_equal

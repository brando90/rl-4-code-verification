import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Nat := min xs.length ys.length
theorem spec_le_left (xs ys : List Int) : solution xs ys ≤ xs.length := by simp [solution]
theorem test_short_left : solution [1] [2, 3] = 1 := by decide
theorem test_empty : solution [] [2] = 0 := by decide
end Tiny
#print axioms Tiny.spec_le_left
#print axioms Tiny.test_short_left
#print axioms Tiny.test_empty

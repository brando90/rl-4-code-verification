import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Bool := xs.length <= ys.length
theorem spec_true_iff (xs ys : List Int) : solution xs ys = true ↔ xs.length ≤ ys.length := by simp [solution]
theorem test_true : solution [1] [2, 3] = true := by decide
theorem test_false : solution [1, 2] [3] = false := by decide
end Tiny

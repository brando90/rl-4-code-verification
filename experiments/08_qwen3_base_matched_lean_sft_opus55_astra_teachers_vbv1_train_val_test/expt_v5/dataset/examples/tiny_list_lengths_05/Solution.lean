import Mathlib
namespace Tiny
def solution (xs : List Int) : Nat := xs.reverse.length
theorem spec_reverse (xs : List Int) : solution xs = xs.length := by simp [solution]
theorem test_empty : solution [] = 0 := by decide
theorem test_many : solution [1, -2, 3] = 3 := by decide
end Tiny

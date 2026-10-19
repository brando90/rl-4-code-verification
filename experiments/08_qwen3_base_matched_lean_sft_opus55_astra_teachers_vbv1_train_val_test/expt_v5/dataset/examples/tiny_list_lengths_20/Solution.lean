import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Nat := (xs ++ ys).length - xs.length
theorem spec_right_length (xs ys : List Int) : solution xs ys = ys.length := by simp [solution]
theorem test_empty : solution [] [1, 2] = 2 := by decide
theorem test_many : solution [1, 2] [-3, 4, 5] = 3 := by decide
end Tiny

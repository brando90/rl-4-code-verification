import Mathlib
namespace Tiny
def solution (xs : List Int) : Nat := xs.count 0
theorem spec_append (xs ys : List Int) :
    solution (xs ++ ys) = solution xs + solution ys := by simp [solution]
theorem test_zeros : solution [0, -1, 0] = 2 := by decide
theorem test_empty : solution [] = 0 := by decide
end Tiny

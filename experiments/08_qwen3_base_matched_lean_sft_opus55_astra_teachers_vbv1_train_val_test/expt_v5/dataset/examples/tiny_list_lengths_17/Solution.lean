import Mathlib
namespace Tiny
def solution (xs ys zs : List Int) : Nat := xs.length + ys.length + zs.length
theorem spec_empty_middle (xs zs : List Int) : solution xs [] zs = xs.length + zs.length := by simp [solution]
theorem test_empty : solution [] [] [] = 0 := by decide
theorem test_many : solution [1] [2, 3] [-4] = 4 := by decide
end Tiny

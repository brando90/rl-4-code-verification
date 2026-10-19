import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Int := (x :: xs).sum
theorem spec_add_head (x : Int) (xs : List Int) : solution x xs = x + xs.sum := by rfl
theorem test_empty : solution 4 [] = 4 := by decide
theorem test_mixed : solution (-2) [5, 1] = 4 := by decide
end Tiny

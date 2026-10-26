import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : Int := (xs.take n).sum + (xs.drop n).sum
theorem spec_partition (n : Nat) (xs : List Int) : solution n xs = xs.sum := by
  simpa [solution] using (sum_take_add_sum_drop xs n)
theorem test_empty : solution 3 [] = 0 := by decide
theorem test_split : solution 2 [3, -5, 2] = 0 := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : Nat := (xs.take n).length + (xs.drop n).length
theorem spec_partition (n : Nat) (xs : List Int) : solution n xs = xs.length := by
  simp [solution]
  omega
theorem test_short : solution 2 [1, 2, 3] = 3 := by decide
theorem test_long : solution 8 [1, 2] = 2 := by decide
end Tiny

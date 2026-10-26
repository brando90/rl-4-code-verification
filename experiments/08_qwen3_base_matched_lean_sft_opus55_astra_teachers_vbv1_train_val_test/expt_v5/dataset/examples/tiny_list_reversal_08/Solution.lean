import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : List Int := (xs.take n).reverse
theorem spec_zero (xs : List Int) : solution 0 xs = [] := by simp [solution]
theorem test_empty : solution 3 [] = [] := by decide
theorem test_prefix : solution 2 [1, 2, 3] = [2, 1] := by decide
end Tiny

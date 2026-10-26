import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : List Int := (xs.drop n).reverse
theorem spec_zero (xs : List Int) : solution 0 xs = xs.reverse := by simp [solution]
theorem test_empty : solution 3 [] = [] := by decide
theorem test_suffix : solution 2 [1, 2, 3, 4] = [4, 3] := by decide
end Tiny

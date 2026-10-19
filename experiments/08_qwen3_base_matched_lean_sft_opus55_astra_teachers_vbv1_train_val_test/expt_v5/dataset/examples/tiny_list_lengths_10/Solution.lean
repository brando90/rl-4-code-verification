import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : Nat := n * xs.length
theorem spec_zero (xs : List Int) : solution 0 xs = 0 := by simp [solution]
theorem test_empty : solution 4 [] = 0 := by decide
theorem test_repeat : solution 3 [1, -2] = 6 := by decide
end Tiny

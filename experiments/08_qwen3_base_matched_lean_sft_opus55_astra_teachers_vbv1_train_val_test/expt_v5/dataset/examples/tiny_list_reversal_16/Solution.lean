import Mathlib
namespace Tiny
def solution (xs : List Int) : Bool := decide (xs = xs.reverse)
theorem spec_palindrome (xs : List Int) : solution xs = true ↔ xs = xs.reverse := by simp [solution]
theorem test_empty : solution [] = true := by decide
theorem test_nonpalindrome : solution [1, 2] = false := by decide
end Tiny

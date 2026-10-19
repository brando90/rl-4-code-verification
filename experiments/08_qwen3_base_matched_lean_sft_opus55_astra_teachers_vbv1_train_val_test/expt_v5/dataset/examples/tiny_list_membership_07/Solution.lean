import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs : List Int) : Bool := (xs.take n).contains x
theorem spec_prefix (x : Int) (n : Nat) (xs : List Int) : solution x n xs = true ↔ x ∈ xs.take n := by simp [solution]
theorem test_in_prefix : solution 2 2 [1, 2, 3] = true := by decide
theorem test_after_prefix : solution 3 2 [1, 2, 3] = false := by decide
end Tiny

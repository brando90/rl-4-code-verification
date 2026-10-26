import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs : List Int) : Bool := (xs.drop n).contains x
theorem spec_suffix (x : Int) (n : Nat) (xs : List Int) : solution x n xs = true ↔ x ∈ xs.drop n := by simp [solution]
theorem test_before_suffix : solution 1 1 [1, 2, 3] = false := by decide
theorem test_in_suffix : solution 3 1 [1, 2, 3] = true := by decide
end Tiny
#print axioms Tiny.spec_suffix
#print axioms Tiny.test_before_suffix
#print axioms Tiny.test_in_suffix

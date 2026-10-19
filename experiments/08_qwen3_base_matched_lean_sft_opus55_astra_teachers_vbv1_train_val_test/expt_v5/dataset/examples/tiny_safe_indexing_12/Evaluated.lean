import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs : List Int) : Bool :=
  match xs.get? n with
  | some y => y == x
  | none => false
theorem spec_empty (x : Int) (n : Nat) : solution x n [] = false := by rfl
theorem test_match : solution 3 1 [2, 3] = true := by decide
theorem test_missing : solution 3 2 [2] = false := by decide
end Tiny
#print axioms Tiny.spec_empty
#print axioms Tiny.test_match
#print axioms Tiny.test_missing

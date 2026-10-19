import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) : List Int := (List.range n).map fun a => a + x
theorem spec_length (x : Int) (n : Nat) : (solution x n).length = n := by simp [solution]
theorem test_positive : solution 5 3 = [5, 6, 7] := by decide
theorem test_negative : solution (-2) 3 = [-2, -1, 0] := by decide
end Tiny
#print axioms Tiny.spec_length
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative

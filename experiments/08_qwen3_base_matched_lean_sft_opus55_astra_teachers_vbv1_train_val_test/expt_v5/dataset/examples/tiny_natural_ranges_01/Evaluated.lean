import Mathlib
namespace Tiny
def solution (n : Nat) : List Int := (List.range n).map Int.ofNat
theorem spec_length (n : Nat) : (solution n).length = n := by simp [solution]
theorem test_empty : solution 0 = [] := by decide
theorem test_three : solution 3 = [0, 1, 2] := by decide
end Tiny
#print axioms Tiny.spec_length
#print axioms Tiny.test_empty
#print axioms Tiny.test_three

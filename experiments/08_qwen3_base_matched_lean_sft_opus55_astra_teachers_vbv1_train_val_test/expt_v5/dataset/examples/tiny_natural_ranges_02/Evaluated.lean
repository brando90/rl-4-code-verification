import Mathlib
namespace Tiny
def solution (n : Nat) : List Int := (List.range (n + 1)).map Int.ofNat
theorem spec_length (n : Nat) : (solution n).length = n + 1 := by simp [solution]
theorem test_zero : solution 0 = [0] := by decide
theorem test_two : solution 2 = [0, 1, 2] := by decide
end Tiny
#print axioms Tiny.spec_length
#print axioms Tiny.test_zero
#print axioms Tiny.test_two

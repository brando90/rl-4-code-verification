import Mathlib
namespace Tiny
def solution (n : Nat) : List Int := List.replicate n 0
theorem spec_length (n : Nat) : (solution n).length = n := by simp [solution]
theorem test_zero : solution 0 = [] := by decide
theorem test_repeat : solution 3 = [0, 0, 0] := by decide
end Tiny
#print axioms Tiny.spec_length
#print axioms Tiny.test_zero
#print axioms Tiny.test_repeat

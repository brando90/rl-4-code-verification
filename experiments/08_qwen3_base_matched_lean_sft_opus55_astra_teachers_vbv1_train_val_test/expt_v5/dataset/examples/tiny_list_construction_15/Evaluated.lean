import Mathlib
namespace Tiny
def solution (n : Nat) : List Bool := List.replicate n true
theorem spec_length (n : Nat) : (solution n).length = n := by simp [solution]
theorem test_zero : solution 0 = [] := by decide
theorem test_repeat : solution 3 = [true, true, true] := by decide
end Tiny
#print axioms Tiny.spec_length
#print axioms Tiny.test_zero
#print axioms Tiny.test_repeat

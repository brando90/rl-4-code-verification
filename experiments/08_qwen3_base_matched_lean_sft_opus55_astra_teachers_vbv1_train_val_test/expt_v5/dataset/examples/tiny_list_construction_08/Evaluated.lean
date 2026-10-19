import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) : List Int := List.replicate n x
theorem spec_length (x : Int) (n : Nat) : (solution x n).length = n := by simp [solution]
theorem test_zero : solution 3 0 = [] := by decide
theorem test_repeat : solution (-2) 3 = [-2, -2, -2] := by decide
end Tiny
#print axioms Tiny.spec_length
#print axioms Tiny.test_zero
#print axioms Tiny.test_repeat

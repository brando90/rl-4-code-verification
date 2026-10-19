import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : Int := (n : Int) * xs.sum
theorem spec_zero (xs : List Int) : solution 0 xs = 0 := by simp [solution]
theorem test_empty : solution 4 [] = 0 := by decide
theorem test_repeat : solution 3 [2, -1] = 3 := by decide
end Tiny
#print axioms Tiny.spec_zero
#print axioms Tiny.test_empty
#print axioms Tiny.test_repeat

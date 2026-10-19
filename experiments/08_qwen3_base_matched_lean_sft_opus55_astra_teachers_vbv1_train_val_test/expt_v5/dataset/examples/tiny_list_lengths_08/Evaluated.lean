import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : Nat := (xs.drop n).length
theorem spec_zero (xs : List Int) : solution 0 xs = xs.length := by simp [solution]
theorem test_short : solution 2 [1, 2, 3] = 1 := by decide
theorem test_long : solution 8 [1, 2] = 0 := by decide
end Tiny
#print axioms Tiny.spec_zero
#print axioms Tiny.test_short
#print axioms Tiny.test_long

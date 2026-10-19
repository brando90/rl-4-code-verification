import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : List Int := xs.drop n
theorem spec_zero (xs : List Int) : solution 0 xs = xs := by rfl
theorem test_suffix : solution 2 [1, 2, 3] = [3] := by decide
theorem test_long : solution 5 [1, 2] = [] := by decide
end Tiny
#print axioms Tiny.spec_zero
#print axioms Tiny.test_suffix
#print axioms Tiny.test_long

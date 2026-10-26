import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : List Int := xs.take n
theorem spec_zero (xs : List Int) : solution 0 xs = [] := by rfl
theorem test_prefix : solution 2 [1, 2, 3] = [1, 2] := by decide
theorem test_long : solution 5 [1, 2] = [1, 2] := by decide
end Tiny
#print axioms Tiny.spec_zero
#print axioms Tiny.test_prefix
#print axioms Tiny.test_long

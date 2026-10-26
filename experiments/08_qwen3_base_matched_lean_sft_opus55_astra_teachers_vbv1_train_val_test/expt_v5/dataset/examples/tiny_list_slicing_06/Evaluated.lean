import Mathlib
namespace Tiny
def solution (n k : Nat) (xs : List Int) : List Int := (xs.drop n).drop k
theorem spec_zero (k : Nat) (xs : List Int) : solution 0 k xs = xs.drop k := by rfl
theorem test_drops : solution 1 2 [1, 2, 3, 4] = [4] := by decide
theorem test_past_end : solution 5 1 [1, 2] = [] := by decide
end Tiny
#print axioms Tiny.spec_zero
#print axioms Tiny.test_drops
#print axioms Tiny.test_past_end

import Mathlib
namespace Tiny
def solution (n k : Nat) (xs : List Int) : List Int := (xs.drop n).take k
theorem spec_zero (k : Nat) (xs : List Int) : solution 0 k xs = xs.take k := by rfl
theorem test_window : solution 1 2 [1, 2, 3, 4] = [2, 3] := by decide
theorem test_past_end : solution 5 2 [1, 2] = [] := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (n k : Nat) (xs : List Int) : Int := ((xs.drop n).take k).sum
theorem spec_zero (k : Nat) (xs : List Int) : solution 0 k xs = (xs.take k).sum := by rfl
theorem test_window : solution 1 2 [1, 2, 3, 4] = 5 := by decide
theorem test_past_end : solution 5 2 [1, 2] = 0 := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs : List Int) : Int := (xs.take n).getLastD x
theorem spec_zero (x : Int) (xs : List Int) : solution x 0 xs = x := by rfl
theorem test_prefix_last : solution 9 2 [2, 3, 4] = 3 := by decide
theorem test_default : solution 9 0 [2, 3] = 9 := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (n : Nat) (xs ys : List Int) : List Int := xs.take n ++ ys
theorem spec_zero (xs ys : List Int) : solution 0 xs ys = ys := by rfl
theorem test_prefix : solution 2 [1, 2, 3] [4] = [1, 2, 4] := by decide
theorem test_long : solution 5 [1, 2] [3] = [1, 2, 3] := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (n : Nat) (xs ys : List Int) : List Int := xs.drop n ++ ys
theorem spec_zero (xs ys : List Int) : solution 0 xs ys = xs ++ ys := by rfl
theorem test_suffix : solution 2 [1, 2, 3] [4] = [3, 4] := by decide
theorem test_long : solution 5 [1, 2] [3] = [3] := by decide
end Tiny

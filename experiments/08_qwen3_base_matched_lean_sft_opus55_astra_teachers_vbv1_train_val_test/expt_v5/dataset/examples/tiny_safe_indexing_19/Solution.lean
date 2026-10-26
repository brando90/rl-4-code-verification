import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : List Int := (xs.drop n).take 1
theorem spec_zero (xs : List Int) : solution 0 xs = xs.take 1 := by rfl
theorem test_index : solution 1 [2, 3] = [3] := by decide
theorem test_missing : solution 2 [2] = [] := by decide
end Tiny

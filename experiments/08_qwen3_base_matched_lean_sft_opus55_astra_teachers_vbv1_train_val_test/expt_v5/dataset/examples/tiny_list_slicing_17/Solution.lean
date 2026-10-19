import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs : List Int) : List Int :=
  (xs.take n).map (fun a => a + x)
theorem spec_zero (x : Int) (xs : List Int) : solution x 0 xs = [] := by rfl
theorem test_prefix : solution 3 2 [1, -2, 4] = [4, 1] := by decide
theorem test_long : solution (-1) 5 [1, 2] = [0, 1] := by decide
end Tiny

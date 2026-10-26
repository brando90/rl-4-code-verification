import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : List Int :=
  (xs.drop n).filter (fun a => decide (a > 0))
theorem spec_zero (xs : List Int) : solution 0 xs = xs.filter (fun a => decide (a > 0)) := by rfl
theorem test_filters_suffix : solution 1 [-1, 2, 0, 3] = [2, 3] := by decide
theorem test_empty : solution 5 [1, 2] = [] := by decide
end Tiny

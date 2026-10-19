import Mathlib
namespace Tiny
def solution (n k : Nat) (xs : List Int) : List Int := (xs.take n).take k
theorem spec_zero (k : Nat) (xs : List Int) : solution 0 k xs = [] := by
  simp [solution]
theorem test_shorter_second : solution 3 2 [1, 2, 3, 4] = [1, 2] := by decide
theorem test_shorter_first : solution 1 5 [1, 2, 3] = [1] := by decide
end Tiny

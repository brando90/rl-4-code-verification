import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : List Int := xs.take n ++ xs.drop n
theorem spec_split (n : Nat) (xs : List Int) : solution n xs = xs := by
  simp [solution]
theorem test_middle : solution 1 [4, 5, 6] = [4, 5, 6] := by decide
theorem test_long : solution 5 [1, 2] = [1, 2] := by decide
end Tiny

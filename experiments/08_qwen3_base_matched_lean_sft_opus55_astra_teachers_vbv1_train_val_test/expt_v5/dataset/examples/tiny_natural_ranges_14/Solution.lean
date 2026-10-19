import Mathlib
namespace Tiny
def solution (n k : Nat) : List Int := ((List.range n).take k).map Int.ofNat
theorem spec_zero_take (n : Nat) : solution n 0 = [] := by simp [solution]
theorem test_prefix : solution 5 3 = [0, 1, 2] := by decide
theorem test_long_prefix : solution 3 5 = [0, 1, 2] := by decide
end Tiny

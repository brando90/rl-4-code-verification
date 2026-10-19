import Mathlib
namespace Tiny
def solution (n k : Nat) : List Int := ((List.range n).filter (· < k)).map Int.ofNat
theorem spec_zero_cutoff (n : Nat) : solution n 0 = [] := by simp [solution]
theorem test_cutoff : solution 5 3 = [0, 1, 2] := by decide
theorem test_large_cutoff : solution 3 5 = [0, 1, 2] := by decide
end Tiny

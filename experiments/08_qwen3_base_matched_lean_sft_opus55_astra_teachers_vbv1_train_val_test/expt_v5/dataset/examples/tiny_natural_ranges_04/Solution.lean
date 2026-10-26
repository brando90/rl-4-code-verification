import Mathlib
namespace Tiny
def solution (n : Nat) : List Int := (List.range n).reverse.map Int.ofNat
theorem spec_length (n : Nat) : (solution n).length = n := by simp [solution]
theorem test_empty : solution 0 = [] := by decide
theorem test_reverse : solution 4 = [3, 2, 1, 0] := by decide
end Tiny

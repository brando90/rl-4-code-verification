import Mathlib
namespace Tiny
def solution (n : Nat) : List Int := (List.range n).map fun a => a * 2
theorem spec_length (n : Nat) : (solution n).length = n := by simp [solution]
theorem test_empty : solution 0 = [] := by decide
theorem test_four : solution 4 = [0, 2, 4, 6] := by decide
end Tiny

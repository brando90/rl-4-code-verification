import Mathlib
namespace Tiny
def solution (n : Nat) : List Int := (List.range n).map fun a => a * 2 + 1
theorem spec_length (n : Nat) : (solution n).length = n := by simp [solution]
theorem test_empty : solution 0 = [] := by decide
theorem test_three : solution 3 = [1, 3, 5] := by decide
end Tiny

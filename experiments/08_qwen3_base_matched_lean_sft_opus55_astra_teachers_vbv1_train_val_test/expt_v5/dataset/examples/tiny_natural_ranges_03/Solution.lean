import Mathlib
namespace Tiny
def solution (n k : Nat) : List Int := (List.range k).map fun i => n + i
theorem spec_length (n k : Nat) : (solution n k).length = k := by simp [solution]
theorem test_empty : solution 4 0 = [] := by decide
theorem test_range : solution 2 3 = [2, 3, 4] := by decide
end Tiny

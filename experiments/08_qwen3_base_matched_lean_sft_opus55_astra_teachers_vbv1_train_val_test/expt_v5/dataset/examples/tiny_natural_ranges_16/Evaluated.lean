import Mathlib
namespace Tiny
def solution (n k : Nat) : List Int := (List.range n).map Int.ofNat ++ (List.range k).map Int.ofNat
theorem spec_length (n k : Nat) : (solution n k).length = n + k := by simp [solution]
theorem test_left_empty : solution 0 3 = [0, 1, 2] := by decide
theorem test_join : solution 3 2 = [0, 1, 2, 0, 1] := by decide
end Tiny
#print axioms Tiny.spec_length
#print axioms Tiny.test_left_empty
#print axioms Tiny.test_join

import Mathlib
namespace Tiny
def solution (n k : Nat) : List Int := ((List.range n).drop k).map Int.ofNat
theorem spec_zero_drop (n : Nat) : solution n 0 = (List.range n).map Int.ofNat := by simp [solution]
theorem test_suffix : solution 5 3 = [3, 4] := by decide
theorem test_long_drop : solution 3 5 = [] := by decide
end Tiny
#print axioms Tiny.spec_zero_drop
#print axioms Tiny.test_suffix
#print axioms Tiny.test_long_drop

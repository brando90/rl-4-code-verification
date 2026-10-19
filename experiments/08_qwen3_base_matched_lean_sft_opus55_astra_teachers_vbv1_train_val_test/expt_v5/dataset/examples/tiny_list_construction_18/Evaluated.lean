import Mathlib
namespace Tiny
def solution (xs : List Int) : List Nat := [xs.length]
theorem spec_head (xs : List Int) : (solution xs).head? = some xs.length := by simp [solution]
theorem test_empty : solution [] = [0] := by decide
theorem test_length : solution [2, -1, 4] = [3] := by decide
end Tiny
#print axioms Tiny.spec_head
#print axioms Tiny.test_empty
#print axioms Tiny.test_length

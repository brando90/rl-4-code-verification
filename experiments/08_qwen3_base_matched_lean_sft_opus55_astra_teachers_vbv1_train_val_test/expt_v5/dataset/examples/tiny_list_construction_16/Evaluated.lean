import Mathlib
namespace Tiny
def solution (pair : Int × Int) : List Int := [pair.1, pair.2]
theorem spec_head (pair : Int × Int) : (solution pair).head? = some pair.1 := by simp [solution]
theorem test_positive : solution (2, 3) = [2, 3] := by decide
theorem test_negative : solution (-1, 0) = [-1, 0] := by decide
end Tiny
#print axioms Tiny.spec_head
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative

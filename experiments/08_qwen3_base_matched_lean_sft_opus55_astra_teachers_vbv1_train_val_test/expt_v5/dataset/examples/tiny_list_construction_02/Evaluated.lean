import Mathlib
namespace Tiny
def solution (x : Int) : List Int := [x]
theorem spec_head (x : Int) : (solution x).head? = some x := by simp [solution]
theorem test_positive : solution 4 = [4] := by decide
theorem test_negative : solution (-2) = [-2] := by decide
end Tiny
#print axioms Tiny.spec_head
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative

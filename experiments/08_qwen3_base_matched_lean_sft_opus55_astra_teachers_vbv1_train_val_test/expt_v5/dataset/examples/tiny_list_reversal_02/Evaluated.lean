import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs.reverse.reverse
theorem spec_identity (xs : List Int) : solution xs = xs := by simp [solution]
theorem test_empty : solution [] = [] := by decide
theorem test_order : solution [1, -2, 3] = [1, -2, 3] := by decide
end Tiny
#print axioms Tiny.spec_identity
#print axioms Tiny.test_empty
#print axioms Tiny.test_order

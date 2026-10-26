import Mathlib
namespace Tiny
def solution (xs : List Int) : Int := (xs.map abs).sum
theorem spec_cons (a : Int) (xs : List Int) : solution (a :: xs) = abs a + solution xs := by rfl
theorem test_empty : solution [] = 0 := by decide
theorem test_mixed : solution [3, -5, 2] = 10 := by decide
end Tiny
#print axioms Tiny.spec_cons
#print axioms Tiny.test_empty
#print axioms Tiny.test_mixed

import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Int := (xs ++ ys).sum
theorem spec_append (xs ys : List Int) : solution xs ys = xs.sum + ys.sum := by simp [solution]
theorem test_empty : solution [] [1, 2] = 3 := by decide
theorem test_mixed : solution [3, -1] [2] = 4 := by decide
end Tiny
#print axioms Tiny.spec_append
#print axioms Tiny.test_empty
#print axioms Tiny.test_mixed

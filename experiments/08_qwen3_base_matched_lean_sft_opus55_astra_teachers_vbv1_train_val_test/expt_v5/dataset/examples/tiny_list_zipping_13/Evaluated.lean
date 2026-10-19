import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Int := ((xs.zip ys).map fun p => p.1 + p.2).sum
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = a + b + solution xs ys := rfl
theorem test_sum : solution [1, -2] [3, 4] = 6 := by decide
theorem test_empty : solution [] [3] = 0 := by decide
end Tiny
#print axioms Tiny.spec_cons
#print axioms Tiny.test_sum
#print axioms Tiny.test_empty

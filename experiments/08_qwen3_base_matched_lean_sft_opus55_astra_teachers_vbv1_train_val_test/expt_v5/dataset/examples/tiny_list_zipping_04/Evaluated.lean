import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := (xs.zip ys).map fun p => p.1 * p.2
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = (a * b) :: solution xs ys := rfl
theorem test_product : solution [2, -2] [3, 4] = [6, -8] := by decide
theorem test_truncates : solution [2, 5] [3] = [6] := by decide
end Tiny
#print axioms Tiny.spec_cons
#print axioms Tiny.test_product
#print axioms Tiny.test_truncates

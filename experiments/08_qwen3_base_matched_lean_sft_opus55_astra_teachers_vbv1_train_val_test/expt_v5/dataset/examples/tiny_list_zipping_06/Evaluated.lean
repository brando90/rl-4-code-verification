import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := (xs.zip ys).map fun p => max p.1 p.2
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = max a b :: solution xs ys := rfl
theorem test_maximum : solution [2, -2] [3, -4] = [3, -2] := by decide
theorem test_empty : solution [2] [] = [] := by decide
end Tiny
#print axioms Tiny.spec_cons
#print axioms Tiny.test_maximum
#print axioms Tiny.test_empty

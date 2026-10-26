import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Bool := (xs.zip ys).map fun p => p.1 == p.2
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = (a == b) :: solution xs ys := rfl
theorem test_equalities : solution [1, -2] [1, 2] = [true, false] := by decide
theorem test_empty : solution [] [1] = [] := by decide
end Tiny
#print axioms Tiny.spec_cons
#print axioms Tiny.test_equalities
#print axioms Tiny.test_empty

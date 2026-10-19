import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := (xs.zip ys).map fun p => min p.1 p.2
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = min a b :: solution xs ys := rfl
theorem test_minimum : solution [2, -2] [3, -4] = [2, -4] := by decide
theorem test_empty : solution [] [3] = [] := by decide
end Tiny
#print axioms Tiny.spec_cons
#print axioms Tiny.test_minimum
#print axioms Tiny.test_empty

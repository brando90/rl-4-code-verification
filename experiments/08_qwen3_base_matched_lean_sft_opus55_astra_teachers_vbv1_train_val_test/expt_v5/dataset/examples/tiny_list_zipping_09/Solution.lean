import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := (xs.zip ys).map Prod.fst
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = a :: solution xs ys := rfl
theorem test_lefts : solution [1, 2] [3] = [1] := by decide
theorem test_empty : solution [] [3] = [] := by decide
end Tiny

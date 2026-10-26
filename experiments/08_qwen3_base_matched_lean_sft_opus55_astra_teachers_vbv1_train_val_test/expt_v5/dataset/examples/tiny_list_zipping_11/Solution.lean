import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List (Int × Int) := (xs.zip ys).map fun p => (p.2, p.1)
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = (b, a) :: solution xs ys := rfl
theorem test_swaps : solution [1, 2] [3] = [(3, 1)] := by decide
theorem test_empty : solution [] [3] = [] := by decide
end Tiny

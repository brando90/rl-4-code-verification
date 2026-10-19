import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := (xs.zip ys).map fun p => p.1 - p.2
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = (a - b) :: solution xs ys := rfl
theorem test_difference : solution [1, -2] [3, 4] = [-2, -6] := by decide
theorem test_empty : solution [] [3] = [] := by decide
end Tiny

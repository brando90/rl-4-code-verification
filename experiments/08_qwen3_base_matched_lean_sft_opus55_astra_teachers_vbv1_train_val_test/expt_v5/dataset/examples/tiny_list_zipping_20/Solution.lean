import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := (xs.zip ys).map fun p => max (p.1 - p.2) (p.2 - p.1)
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = max (a - b) (b - a) :: solution xs ys := rfl
theorem test_absolute_difference : solution [-2, 4] [-4, -4] = [2, 8] := by decide
theorem test_empty : solution [] [3] = [] := by decide
end Tiny

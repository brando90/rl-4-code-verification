import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Bool := (xs.zip ys).map fun p => decide (p.1 <= p.2)
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = decide (a <= b) :: solution xs ys := rfl
theorem test_order : solution [1, 3] [1, 2] = [true, false] := by decide
theorem test_empty : solution [1] [] = [] := by decide
end Tiny

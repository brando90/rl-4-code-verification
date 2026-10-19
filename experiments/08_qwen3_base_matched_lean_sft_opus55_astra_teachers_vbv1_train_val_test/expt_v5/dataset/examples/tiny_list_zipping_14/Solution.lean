import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Bool := (xs.zip ys).all fun p => p.1 == p.2
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = ((a == b) && solution xs ys) := rfl
theorem test_all_equal : solution [1, -2] [1, -2, 3] = true := by decide
theorem test_difference : solution [1, 2] [1, 3] = false := by decide
end Tiny

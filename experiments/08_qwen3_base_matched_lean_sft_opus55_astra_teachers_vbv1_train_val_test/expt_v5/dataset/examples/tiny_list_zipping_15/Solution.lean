import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Bool := (xs.zip ys).any fun p => p.1 == p.2
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = ((a == b) || solution xs ys) := rfl
theorem test_one_equal : solution [1, 2] [3, 2] = true := by decide
theorem test_none_equal : solution [1, 2] [3, 4] = false := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List (Int × Int) := xs.zip ys
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = (a, b) :: solution xs ys := rfl
theorem test_truncates : solution [1, 2] [3] = [(1, 3)] := by decide
theorem test_empty : solution [] [3] = [] := by decide
end Tiny

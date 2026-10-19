import Mathlib
namespace Tiny
def solution (xs : List Int) : List (Int × Int) := xs.zip xs
theorem spec_cons (a : Int) (xs : List Int) : solution (a :: xs) = (a, a) :: solution xs := rfl
theorem test_pairs : solution [1, -2] = [(1, 1), (-2, -2)] := by decide
theorem test_empty : solution [] = [] := by decide
end Tiny

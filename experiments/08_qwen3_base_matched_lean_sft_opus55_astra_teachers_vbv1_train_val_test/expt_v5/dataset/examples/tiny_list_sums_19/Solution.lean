import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Int := (List.zipWith (fun a b => a - b) xs ys).sum
theorem spec_cons (a b : Int) (xs ys : List Int) : solution (a :: xs) (b :: ys) = a - b + solution xs ys := by rfl
theorem test_empty : solution [] [1, 2] = 0 := by decide
theorem test_truncate : solution [3, -5, 2] [4, 1] = -7 := by decide
end Tiny

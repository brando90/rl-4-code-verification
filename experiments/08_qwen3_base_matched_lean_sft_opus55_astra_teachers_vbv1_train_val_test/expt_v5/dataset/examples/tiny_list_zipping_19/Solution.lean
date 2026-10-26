import Mathlib
namespace Tiny
def solution (x : Int) (xs ys : List Int) : List (Int × Int) := (xs.zip ys).map fun p => (p.1 + x, p.2 + x)
theorem spec_cons (x a b : Int) (xs ys : List Int) : solution x (a :: xs) (b :: ys) = (a + x, b + x) :: solution x xs ys := rfl
theorem test_shift : solution 2 [1, -2] [3, 4] = [(3, 5), (0, 6)] := by decide
theorem test_empty : solution 2 [] [3] = [] := by decide
end Tiny

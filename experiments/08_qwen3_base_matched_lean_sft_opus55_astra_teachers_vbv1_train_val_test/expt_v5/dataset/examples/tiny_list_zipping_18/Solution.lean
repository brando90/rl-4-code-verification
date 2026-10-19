import Mathlib
namespace Tiny
def solution (n : Nat) (xs ys : List Int) : List (Int × Int) := (xs.take n).zip (ys.take n)
theorem spec_cons (n : Nat) (a b : Int) (xs ys : List Int) : solution (n + 1) (a :: xs) (b :: ys) = (a, b) :: solution n xs ys := by
  rfl
theorem test_limit : solution 1 [1, 2] [3, 4] = [(1, 3)] := by decide
theorem test_zero : solution 0 [1] [3] = [] := by decide
end Tiny

import Mathlib
namespace Tiny
def solution (n : Nat) (xs : List Int) : Int := (xs.take n).sum
theorem spec_cons_succ (n : Nat) (x : Int) (xs : List Int) : solution (n + 1) (x :: xs) = x + solution n xs := by rfl
theorem test_empty : solution 3 [] = 0 := by decide
theorem test_prefix : solution 2 [3, -5, 2] = -2 := by decide
end Tiny

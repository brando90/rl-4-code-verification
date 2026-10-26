import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs : List Int) : Nat := n * xs.count x
theorem spec_succ (x : Int) (n : Nat) (xs : List Int) :
    solution x (n + 1) xs = solution x n xs + xs.count x := by simp [solution, Nat.add_mul]
theorem test_repeated : solution 2 3 [2, 1, 2] = 6 := by decide
theorem test_zero : solution 2 0 [2, 1] = 0 := by decide
end Tiny

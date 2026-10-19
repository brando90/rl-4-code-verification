import Mathlib
namespace Tiny
def solution (x y : Int) : Nat → List Int
  | 0 => []
  | n + 1 => x :: y :: solution x y n
theorem spec_succ (x y : Int) (n : Nat) : solution x y (n + 1) = x :: y :: solution x y n := by rfl
theorem test_zero : solution 1 2 0 = [] := by decide
theorem test_repeat : solution (-1) 3 2 = [-1, 3, -1, 3] := by decide
end Tiny

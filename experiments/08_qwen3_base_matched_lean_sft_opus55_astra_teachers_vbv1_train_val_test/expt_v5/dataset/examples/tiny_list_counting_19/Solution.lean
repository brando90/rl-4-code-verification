import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) (xs : List Int) : Nat := (xs.take n).count x + (xs.drop n).count x
theorem spec_total (x : Int) (n : Nat) (xs : List Int) : solution x n xs = xs.count x := by
  rw [solution, ← List.count_append, xs.take_append_drop]
theorem test_middle : solution 2 2 [2, 1, 2, 2] = 3 := by decide
theorem test_past_end : solution 2 9 [2, 1] = 1 := by decide
end Tiny

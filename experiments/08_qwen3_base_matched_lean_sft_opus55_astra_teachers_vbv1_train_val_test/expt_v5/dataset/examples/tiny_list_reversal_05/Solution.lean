import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : List Int := (xs ++ [x]).reverse
theorem spec_cons (x : Int) (xs : List Int) : solution x xs = x :: xs.reverse := by simp [solution]
theorem test_empty : solution 4 [] = [4] := by decide
theorem test_order : solution 1 [2, 3] = [1, 3, 2] := by decide
end Tiny

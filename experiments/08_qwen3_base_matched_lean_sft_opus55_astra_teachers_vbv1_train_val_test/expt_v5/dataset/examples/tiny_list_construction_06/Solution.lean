import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : List Int := xs ++ [x]
theorem spec_last (x : Int) (xs : List Int) : (solution x xs).getLast? = some x := by simp [solution]
theorem test_empty : solution 5 [] = [5] := by decide
theorem test_order : solution (-1) [2, 3] = [2, 3, -1] := by decide
end Tiny

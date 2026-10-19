import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : List Int := x :: xs
theorem spec_head (x : Int) (xs : List Int) : (solution x xs).head? = some x := by simp [solution]
theorem test_empty : solution 5 [] = [5] := by decide
theorem test_order : solution (-1) [2, 3] = [-1, 2, 3] := by decide
end Tiny

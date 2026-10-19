import Mathlib
namespace Tiny
def solution (x : Int) (xs ys : List Int) : List Int := [x] ++ xs ++ ys
theorem spec_head (x : Int) (xs ys : List Int) : (solution x xs ys).head? = some x := by simp [solution]
theorem test_empty : solution 1 [] [] = [1] := by decide
theorem test_order : solution (-1) [2] [3, 4] = [-1, 2, 3, 4] := by decide
end Tiny
#print axioms Tiny.spec_head
#print axioms Tiny.test_empty
#print axioms Tiny.test_order

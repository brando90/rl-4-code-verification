import Mathlib
namespace Tiny
def solution (x y : Int) (xs : List Int) : List Int := x :: xs ++ [y]
theorem spec_head (x y : Int) (xs : List Int) : (solution x y xs).head? = some x := by simp [solution]
theorem test_empty : solution 1 2 [] = [1, 2] := by decide
theorem test_order : solution (-1) 4 [2, 3] = [-1, 2, 3, 4] := by decide
end Tiny
#print axioms Tiny.spec_head
#print axioms Tiny.test_empty
#print axioms Tiny.test_order

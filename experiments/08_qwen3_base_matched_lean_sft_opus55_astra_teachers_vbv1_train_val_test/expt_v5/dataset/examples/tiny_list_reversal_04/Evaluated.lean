import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : List Int := (x :: xs).reverse
theorem spec_append (x : Int) (xs : List Int) : solution x xs = xs.reverse ++ [x] := by simp [solution]
theorem test_empty : solution 4 [] = [4] := by decide
theorem test_order : solution 1 [2, 3] = [3, 2, 1] := by decide
end Tiny
#print axioms Tiny.spec_append
#print axioms Tiny.test_empty
#print axioms Tiny.test_order

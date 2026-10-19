import Mathlib
namespace Tiny
def solution (x : Int) (xs ys : List Int) : List Int := xs ++ [x] ++ ys
theorem spec_contains (x : Int) (xs ys : List Int) : x ∈ solution x xs ys := by simp [solution]
theorem test_empty : solution 1 [] [] = [1] := by decide
theorem test_order : solution (-1) [2] [3, 4] = [2, -1, 3, 4] := by decide
end Tiny
#print axioms Tiny.spec_contains
#print axioms Tiny.test_empty
#print axioms Tiny.test_order

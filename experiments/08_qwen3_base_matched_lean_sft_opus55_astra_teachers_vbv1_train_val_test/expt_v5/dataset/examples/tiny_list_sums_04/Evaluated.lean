import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Int := (xs ++ [x]).sum
theorem spec_add_last (x : Int) (xs : List Int) : solution x xs = xs.sum + x := by simp [solution]
theorem test_empty : solution 4 [] = 4 := by decide
theorem test_mixed : solution (-2) [5, 1] = 4 := by decide
end Tiny
#print axioms Tiny.spec_add_last
#print axioms Tiny.test_empty
#print axioms Tiny.test_mixed

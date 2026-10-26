import Mathlib
namespace Tiny
def solution (x : Int) (xs : List Int) : Nat := (xs ++ [x]).length
theorem spec_snoc (x : Int) (xs : List Int) : solution x xs = xs.length + 1 := by simp [solution]
theorem test_empty : solution 9 [] = 1 := by decide
theorem test_many : solution (-1) [2, 3] = 3 := by decide
end Tiny
#print axioms Tiny.spec_snoc
#print axioms Tiny.test_empty
#print axioms Tiny.test_many

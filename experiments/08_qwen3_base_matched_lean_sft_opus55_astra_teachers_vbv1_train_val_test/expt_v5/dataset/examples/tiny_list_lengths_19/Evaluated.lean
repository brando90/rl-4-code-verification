import Mathlib
namespace Tiny
def solution (xs : List Int) : Nat := xs.length - 1
theorem spec_snoc (x : Int) (xs : List Int) : solution (xs ++ [x]) = xs.length := by simp [solution]
theorem test_empty : solution [] = 0 := by decide
theorem test_many : solution [1, 2, 3] = 2 := by decide
end Tiny
#print axioms Tiny.spec_snoc
#print axioms Tiny.test_empty
#print axioms Tiny.test_many

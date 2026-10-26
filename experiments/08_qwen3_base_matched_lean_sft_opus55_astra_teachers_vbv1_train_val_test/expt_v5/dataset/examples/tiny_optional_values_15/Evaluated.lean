import Mathlib
namespace Tiny
def solution (xs : List Int) : Option Int := xs.reverse.head?
theorem spec_append (xs : List Int) (x : Int) : solution (xs ++ [x]) = some x := by simp [solution]
theorem test_empty : solution [] = none := by decide
theorem test_values : solution [2, -1] = some (-1) := by decide
end Tiny
#print axioms Tiny.spec_append
#print axioms Tiny.test_empty
#print axioms Tiny.test_values

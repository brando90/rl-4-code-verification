import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Nat := (xs ++ ys).length
theorem spec_length (xs ys : List Int) : solution xs ys = xs.length + ys.length := by simp [solution]
theorem test_empty : solution [] [1, 2] = 2 := by decide
theorem test_values : solution [2, -1] [3] = 3 := by decide
end Tiny
#print axioms Tiny.spec_length
#print axioms Tiny.test_empty
#print axioms Tiny.test_values

import Mathlib
namespace Tiny
def solution (xs ys : List Int) : Nat := (xs ++ ys).length
theorem spec_append (xs ys : List Int) : solution xs ys = xs.length + ys.length := by simp [solution]
theorem test_empty : solution [] [1] = 1 := by decide
theorem test_order : solution [2, 1] [2, 3] = 4 := by decide
end Tiny
#print axioms Tiny.spec_append
#print axioms Tiny.test_empty
#print axioms Tiny.test_order

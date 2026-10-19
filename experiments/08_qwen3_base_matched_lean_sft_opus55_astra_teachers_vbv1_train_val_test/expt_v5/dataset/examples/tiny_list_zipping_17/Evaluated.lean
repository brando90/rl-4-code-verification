import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List (Int × Int) := xs.reverse.zip ys
theorem spec_empty_right (xs : List Int) : solution xs [] = [] := by simp [solution]
theorem test_reverses : solution [1, 2, 3] [4, 5] = [(3, 4), (2, 5)] := by decide
theorem test_empty : solution [] [4] = [] := by decide
end Tiny
#print axioms Tiny.spec_empty_right
#print axioms Tiny.test_reverses
#print axioms Tiny.test_empty

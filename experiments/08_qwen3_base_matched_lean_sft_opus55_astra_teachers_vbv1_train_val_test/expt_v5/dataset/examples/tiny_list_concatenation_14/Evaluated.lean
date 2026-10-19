import Mathlib
namespace Tiny
def solution (xs ys : List Int) : List Int := (xs ++ ys).map fun a => a + 1
theorem spec_length (xs ys : List Int) : (solution xs ys).length = xs.length + ys.length := by simp [solution]
theorem test_empty : solution [] [1, 2] = [2, 3] := by decide
theorem test_values : solution [2, -1] [0] = [3, 0, 1] := by decide
end Tiny
#print axioms Tiny.spec_length
#print axioms Tiny.test_empty
#print axioms Tiny.test_values

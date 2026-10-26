import Mathlib
namespace Tiny
def solution (xs : List Int) : List Int := xs.reverse
theorem spec_length (xs : List Int) : (solution xs).length = xs.length := by simp [solution]
theorem test_empty : solution [] = [] := by decide
theorem test_order : solution [1, -2, 3] = [3, -2, 1] := by decide
end Tiny
#print axioms Tiny.spec_length
#print axioms Tiny.test_empty
#print axioms Tiny.test_order

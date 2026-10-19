import Mathlib
namespace Tiny
def solution (xs : List Int) : Nat := xs.reverse.length
theorem spec_length (xs : List Int) : solution xs = xs.length := by simp [solution]
theorem test_empty : solution [] = 0 := by decide
theorem test_values : solution [1, -3, 4] = 3 := by decide
end Tiny
#print axioms Tiny.spec_length
#print axioms Tiny.test_empty
#print axioms Tiny.test_values

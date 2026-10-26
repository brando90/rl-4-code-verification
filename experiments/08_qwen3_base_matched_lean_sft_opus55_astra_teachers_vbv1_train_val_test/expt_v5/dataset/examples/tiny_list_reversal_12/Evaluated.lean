import Mathlib
namespace Tiny
def solution (xs : List Int) : Int := xs.reverse.sum
theorem spec_sum (xs : List Int) : solution xs = xs.sum := by simp [solution]
theorem test_empty : solution [] = 0 := by decide
theorem test_values : solution [1, -3, 4] = 2 := by decide
end Tiny
#print axioms Tiny.spec_sum
#print axioms Tiny.test_empty
#print axioms Tiny.test_values

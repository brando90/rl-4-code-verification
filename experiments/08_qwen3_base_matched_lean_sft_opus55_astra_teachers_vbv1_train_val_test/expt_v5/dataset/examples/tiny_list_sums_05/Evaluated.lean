import Mathlib
namespace Tiny
def solution (xs : List Int) : Int := xs.reverse.sum
theorem spec_reverse_invariant (xs : List Int) : solution xs = xs.sum := by simp [solution]
theorem test_empty : solution [] = 0 := by decide
theorem test_mixed : solution [3, -5, 2] = 0 := by decide
end Tiny
#print axioms Tiny.spec_reverse_invariant
#print axioms Tiny.test_empty
#print axioms Tiny.test_mixed

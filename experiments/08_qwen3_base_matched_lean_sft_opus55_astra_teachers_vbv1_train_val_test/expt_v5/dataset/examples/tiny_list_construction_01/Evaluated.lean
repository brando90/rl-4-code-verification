import Mathlib
namespace Tiny
def solution : List Int := []
theorem spec_empty (x : Int) : x ∉ solution := by simp [solution]
theorem test_length : solution.length = 0 := by decide
theorem test_value : solution = ([] : List Int) := by decide
end Tiny
#print axioms Tiny.spec_empty
#print axioms Tiny.test_length
#print axioms Tiny.test_value

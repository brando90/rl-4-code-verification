import Mathlib
namespace Tiny
def solution (xs : List Int) (p : Bool) : List Int := xs.filter fun _ => p
theorem spec_true (xs : List Int) : solution xs true = xs := by simp [solution]
theorem spec_false (xs : List Int) : solution xs false = [] := by simp [solution]
theorem test_true : solution [1, -2] true = [1, -2] := by decide
theorem test_false : solution [1, -2] false = [] := by decide
end Tiny
#print axioms Tiny.spec_true
#print axioms Tiny.spec_false
#print axioms Tiny.test_true
#print axioms Tiny.test_false

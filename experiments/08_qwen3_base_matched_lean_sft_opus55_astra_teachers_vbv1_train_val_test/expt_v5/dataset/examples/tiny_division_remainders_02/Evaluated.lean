import Mathlib
namespace Tiny
def solution (x : Int) : Int := x % 2
theorem spec_even (x : Int) : solution (2 * x) = 0 := by simp [solution]
theorem test_negative : solution (-3) = 1 := by norm_num [solution]
theorem test_even : solution 6 = 0 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_even
#print axioms Tiny.test_negative
#print axioms Tiny.test_even

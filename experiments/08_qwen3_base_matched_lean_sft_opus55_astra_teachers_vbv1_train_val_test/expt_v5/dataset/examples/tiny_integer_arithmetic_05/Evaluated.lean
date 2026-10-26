import Mathlib
namespace Tiny
def solution (x : Int) : Int := |x|
theorem spec_nonnegative (x : Int) : 0 <= solution x := by
  exact abs_nonneg x
theorem test_positive : solution 4 = 4 := by norm_num [solution]
theorem test_negative : solution (-3) = 3 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_nonnegative
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative

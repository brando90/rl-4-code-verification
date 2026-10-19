import Mathlib
namespace Tiny
def solution (x y : Int) : Int := |x - y|
theorem spec_symmetric (x y : Int) : solution x y = solution y x := by
  simp [solution, abs_sub_comm]
theorem test_positive : solution 7 3 = 4 := by norm_num [solution]
theorem test_negative : solution (-2) 5 = 7 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_symmetric
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative

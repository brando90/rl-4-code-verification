import Mathlib
namespace Tiny
def solution (x y z : Int) : Int := x + y + z
theorem spec_reverse (x y z : Int) : solution x y z = solution z y x := by
  simp [solution, add_comm, add_left_comm]
theorem test_positive : solution 1 2 3 = 6 := by norm_num [solution]
theorem test_negative : solution (-4) 1 2 = -1 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_reverse
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative

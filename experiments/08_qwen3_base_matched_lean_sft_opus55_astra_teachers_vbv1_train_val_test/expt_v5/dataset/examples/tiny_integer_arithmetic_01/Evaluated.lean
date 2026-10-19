import Mathlib
namespace Tiny
def solution (x y : Int) : Int := x + y
theorem spec_commutative (x y : Int) : solution x y = solution y x := by
  simp [solution, add_comm]
theorem test_positive : solution 2 3 = 5 := by norm_num [solution]
theorem test_negative : solution (-3) 1 = -2 := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_commutative
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative

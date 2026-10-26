import Mathlib
namespace Tiny
def solution (x y : Int) : Int × Int := (x, y)
theorem spec_first (x y : Int) : (solution x y).1 = x := rfl
theorem test_positive : solution 2 3 = (2, 3) := by norm_num [solution]
theorem test_negative : solution (-2) 4 = (-2, 4) := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_first
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative

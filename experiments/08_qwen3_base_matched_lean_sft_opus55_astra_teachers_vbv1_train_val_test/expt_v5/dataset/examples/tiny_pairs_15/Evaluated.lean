import Mathlib
namespace Tiny
def solution (x : Int) (pair : Int × Int) : Int × Int := (pair.1 * x, pair.2 * x)
theorem spec_zero (pair : Int × Int) : solution 0 pair = (0, 0) := by simp [solution]
theorem test_positive : solution 2 (3, 4) = (6, 8) := by norm_num [solution]
theorem test_negative : solution (-2) (-3, 4) = (6, -8) := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_zero
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative

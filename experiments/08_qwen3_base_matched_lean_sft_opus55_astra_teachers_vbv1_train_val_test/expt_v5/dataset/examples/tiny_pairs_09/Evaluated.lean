import Mathlib
namespace Tiny
def solution (pair : Int × Int) : Int × Int := (pair.1 + 1, pair.2)
theorem spec_second (pair : Int × Int) : (solution pair).2 = pair.2 := rfl
theorem test_positive : solution (2, 3) = (3, 3) := by norm_num [solution]
theorem test_negative : solution (-2, 4) = (-1, 4) := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_second
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative

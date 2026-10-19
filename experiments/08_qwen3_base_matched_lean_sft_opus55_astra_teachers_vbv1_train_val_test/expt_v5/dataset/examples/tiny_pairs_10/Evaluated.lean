import Mathlib
namespace Tiny
def solution (pair : Int × Int) : Int × Int := (pair.1, pair.2 + 1)
theorem spec_first (pair : Int × Int) : (solution pair).1 = pair.1 := rfl
theorem test_positive : solution (2, 3) = (2, 4) := by norm_num [solution]
theorem test_negative : solution (-2, 4) = (-2, 5) := by norm_num [solution]
end Tiny
#print axioms Tiny.spec_first
#print axioms Tiny.test_positive
#print axioms Tiny.test_negative

import Mathlib
namespace Tiny
def solution (pair : Int × Int) : Int := pair.1
theorem spec_first (pair : Int × Int) : solution pair = pair.1 := rfl
theorem test_positive : solution (2, 3) = 2 := by norm_num [solution]
theorem test_negative : solution (-2, 4) = -2 := by norm_num [solution]
end Tiny

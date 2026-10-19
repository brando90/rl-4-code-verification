import Mathlib
namespace Tiny
def solution (pair : Int × Int) : Int := pair.2
theorem spec_second (pair : Int × Int) : solution pair = pair.2 := rfl
theorem test_positive : solution (2, 3) = 3 := by norm_num [solution]
theorem test_negative : solution (-2, 4) = 4 := by norm_num [solution]
end Tiny

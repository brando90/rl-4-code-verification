import Mathlib
namespace Tiny
def solution (x : Int) : Int := -x
theorem spec_involutive (x : Int) : solution (solution x) = x := by
  simp [solution]
theorem test_positive : solution 4 = -4 := by norm_num [solution]
theorem test_negative : solution (-3) = 3 := by norm_num [solution]
end Tiny

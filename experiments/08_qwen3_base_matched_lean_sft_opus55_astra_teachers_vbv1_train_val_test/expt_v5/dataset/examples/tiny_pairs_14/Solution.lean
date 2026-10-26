import Mathlib
namespace Tiny
def solution (x : Int) (pair : Int × Int) : Int × Int := (pair.1 + x, pair.2 + x)
theorem spec_difference (x : Int) (pair : Int × Int) : (solution x pair).1 - (solution x pair).2 = pair.1 - pair.2 := by
  simp [solution]
theorem test_positive : solution 2 (3, 4) = (5, 6) := by norm_num [solution]
theorem test_negative : solution (-2) (-3, 4) = (-5, 2) := by norm_num [solution]
end Tiny

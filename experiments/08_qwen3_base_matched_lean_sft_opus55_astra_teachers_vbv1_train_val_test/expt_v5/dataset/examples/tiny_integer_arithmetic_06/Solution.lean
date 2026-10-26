import Mathlib
namespace Tiny
def solution (x y z : Int) : Int := x + y - z
theorem spec_add_z (x y z : Int) : solution x y z + z = x + y := by
  simp [solution]
theorem test_positive : solution 4 5 3 = 6 := by norm_num [solution]
theorem test_negative : solution (-2) 1 4 = -5 := by norm_num [solution]
end Tiny

import Mathlib
namespace Tiny
def solution (x : Int) : Int × Int := (x / 2, x % 2)
theorem spec_reconstruct (x : Int) : 2 * (solution x).1 + (solution x).2 = x := by
  simpa [solution] using Int.ediv_add_emod x 2
theorem test_negative : solution (-3) = (-2, 1) := by norm_num [solution]
theorem test_positive : solution 7 = (3, 1) := by norm_num [solution]
end Tiny

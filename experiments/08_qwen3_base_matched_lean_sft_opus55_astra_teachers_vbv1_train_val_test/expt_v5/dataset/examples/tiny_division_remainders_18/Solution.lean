import Mathlib
namespace Tiny
def solution (x : Int) : Int := (2 * x + 1) / 2
theorem spec_successor (x : Int) : solution (x + 1) = solution x + 1 := by
  unfold solution
  rw [show 2 * (x + 1) + 1 = (2 * x + 1) + 2 by ring]
  rw [Int.add_ediv_of_dvd_right (by norm_num : (2 : Int) ∣ 2)]
  norm_num
theorem test_negative : solution (-7) = -7 := by norm_num [solution]
theorem test_positive : solution 8 = 8 := by norm_num [solution]
end Tiny

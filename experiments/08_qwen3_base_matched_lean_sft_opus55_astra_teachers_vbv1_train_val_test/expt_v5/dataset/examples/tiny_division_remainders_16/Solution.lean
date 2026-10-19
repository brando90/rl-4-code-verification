import Mathlib
namespace Tiny
def solution (x : Int) : Int := (x + 2) / 2
theorem spec_even (x : Int) : solution (2 * x) = x + 1 := by
  change (2 * x + 2) / 2 = x + 1
  rw [show 2 * x + 2 = 2 * (x + 1) by ring]
  simp
theorem test_negative : solution (-7) = -3 := by norm_num [solution]
theorem test_positive : solution 8 = 5 := by norm_num [solution]
end Tiny

import Mathlib
namespace Tiny
def solution (pair : Int × Int) : Int := pair.1 + pair.2
theorem spec_commutative (pair : Int × Int) : solution (pair.2, pair.1) = solution pair := by
  simp [solution, add_comm]
theorem test_positive : solution (2, 3) = 5 := by norm_num [solution]
theorem test_negative : solution (-2, 4) = 2 := by norm_num [solution]
end Tiny

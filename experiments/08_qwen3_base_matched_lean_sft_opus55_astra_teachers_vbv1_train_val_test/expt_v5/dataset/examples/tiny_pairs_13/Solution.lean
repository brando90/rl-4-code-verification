import Mathlib
namespace Tiny
def solution (x y : Int) : Int × Int := (min x y, max x y)
theorem spec_ordered (x y : Int) : (solution x y).1 ≤ (solution x y).2 := by
  exact min_le_max
theorem test_ordered : solution 2 3 = (2, 3) := by norm_num [solution]
theorem test_reversed : solution 4 (-2) = (-2, 4) := by norm_num [solution]
end Tiny

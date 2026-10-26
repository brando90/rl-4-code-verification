import Mathlib
namespace Tiny
def solution (x y : Int) : Int × Int := (y, x)
theorem spec_swap_twice (x y : Int) : solution (solution x y).1 (solution x y).2 = (x, y) := rfl
theorem test_positive : solution 2 3 = (3, 2) := by norm_num [solution]
theorem test_negative : solution (-2) 4 = (4, -2) := by norm_num [solution]
end Tiny

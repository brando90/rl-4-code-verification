import Mathlib
namespace Tiny
def solution (x y z : Int) : Int := (x + y + z) % 2
theorem spec_swap_ends (x y z : Int) : solution x y z = solution z y x := by
  simp [solution, add_comm, add_left_comm]
theorem test_even_sum : solution 1 2 3 = 0 := by decide
theorem test_odd_sum : solution (-2) 4 5 = 1 := by decide
end Tiny

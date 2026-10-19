import Mathlib
namespace Tiny
def solution (x : Int) : Int := x % 2
theorem spec_range (x : Int) : solution x = 0 ∨ solution x = 1 := by
  simp [solution]
  omega
theorem test_even : solution (-4) = 0 := by decide
theorem test_odd : solution (-3) = 1 := by decide
end Tiny

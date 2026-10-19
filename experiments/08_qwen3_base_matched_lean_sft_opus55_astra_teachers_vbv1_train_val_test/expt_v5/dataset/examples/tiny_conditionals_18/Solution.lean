import Mathlib
namespace Tiny
def solution (x : Int) (n : Nat) : Int := if x >= -(n : Int) then x else -(n : Int)
theorem spec_lower_bound (x : Int) (n : Nat) : -(n : Int) <= solution x n := by
  by_cases h : x >= -(n : Int) <;> simp [solution, h] <;> omega
theorem test_above : solution (-2) 3 = -2 := by decide
theorem test_below : solution (-5) 3 = -3 := by decide
end Tiny

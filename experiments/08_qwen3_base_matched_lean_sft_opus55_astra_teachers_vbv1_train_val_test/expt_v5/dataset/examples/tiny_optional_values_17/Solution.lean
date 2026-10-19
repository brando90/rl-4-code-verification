import Mathlib
namespace Tiny
def solution (x : Int) : Option Int := if x % 2 = 0 then some x else none
theorem spec_even (x : Int) (h : x % 2 = 0) : solution x = some x := by simp [solution, h]
theorem test_even : solution (-2) = some (-2) := by decide
theorem test_odd : solution (-3) = none := by decide
end Tiny

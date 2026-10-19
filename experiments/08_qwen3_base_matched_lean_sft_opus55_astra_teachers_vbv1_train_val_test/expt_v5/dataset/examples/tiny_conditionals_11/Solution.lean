import Mathlib
namespace Tiny
def solution (x y : Int) : Int := if x != 0 then x else y
theorem spec_nonzero (x y : Int) (h : x != 0) : solution x y = x := by
  simp [solution, h]
theorem test_nonzero : solution 3 9 = 3 := by decide
theorem test_zero : solution 0 9 = 9 := by decide
end Tiny

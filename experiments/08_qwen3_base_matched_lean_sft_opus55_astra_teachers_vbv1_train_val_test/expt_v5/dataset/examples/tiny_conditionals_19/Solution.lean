import Mathlib
namespace Tiny
def solution (x y z : Int) : Int := if x >= y && x >= z then x else max y z
theorem spec_largest (x y z : Int) (h₁ : x >= y) (h₂ : x >= z) : solution x y z = x := by
  simp [solution, h₁, h₂]
theorem test_first : solution 5 2 3 = 5 := by decide
theorem test_other : solution 1 5 3 = 5 := by decide
end Tiny

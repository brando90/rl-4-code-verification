import Mathlib
namespace Tiny
def solution (x y z : Int) : Int := if x <= y && x <= z then x else min y z
theorem spec_smallest (x y z : Int) (h₁ : x <= y) (h₂ : x <= z) : solution x y z = x := by
  simp [solution, h₁, h₂]
theorem test_first : solution 1 5 3 = 1 := by decide
theorem test_other : solution 5 1 3 = 1 := by decide
end Tiny
#print axioms Tiny.spec_smallest
#print axioms Tiny.test_first
#print axioms Tiny.test_other

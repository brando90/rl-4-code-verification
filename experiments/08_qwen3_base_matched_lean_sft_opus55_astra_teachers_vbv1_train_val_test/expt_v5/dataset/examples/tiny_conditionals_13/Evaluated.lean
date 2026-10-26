import Mathlib
namespace Tiny
def solution (x y : Int) (p : Bool) : Int := if p then x + y else x - y
theorem spec_true (x y : Int) : solution x y true = x + y := by rfl
theorem test_sum : solution 4 (-2) true = 2 := by decide
theorem test_difference : solution 4 (-2) false = 6 := by decide
end Tiny
#print axioms Tiny.spec_true
#print axioms Tiny.test_sum
#print axioms Tiny.test_difference

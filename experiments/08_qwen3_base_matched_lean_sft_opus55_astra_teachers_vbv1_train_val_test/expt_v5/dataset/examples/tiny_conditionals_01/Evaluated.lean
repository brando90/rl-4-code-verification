import Mathlib
namespace Tiny
def solution (x y : Int) (p : Bool) : Int := if p then x else y
theorem spec_true (x y : Int) : solution x y true = x := by rfl
theorem test_true : solution 2 (-3) true = 2 := by decide
theorem test_false : solution 2 (-3) false = -3 := by decide
end Tiny
#print axioms Tiny.spec_true
#print axioms Tiny.test_true
#print axioms Tiny.test_false

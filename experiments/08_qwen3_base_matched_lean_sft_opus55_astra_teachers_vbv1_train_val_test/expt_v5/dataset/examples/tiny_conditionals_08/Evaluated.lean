import Mathlib
namespace Tiny
def solution (x y : Int) (p : Bool) : Int := if !p then x else y
theorem spec_false (x y : Int) : solution x y false = x := by rfl
theorem test_false : solution 4 9 false = 4 := by decide
theorem test_true : solution 4 9 true = 9 := by decide
end Tiny
#print axioms Tiny.spec_false
#print axioms Tiny.test_false
#print axioms Tiny.test_true

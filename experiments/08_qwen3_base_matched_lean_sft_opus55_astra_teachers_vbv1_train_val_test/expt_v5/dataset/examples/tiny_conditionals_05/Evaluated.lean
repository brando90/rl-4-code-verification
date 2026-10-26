import Mathlib
namespace Tiny
def solution (x : Int) (p : Bool) : Int := if p then x + 1 else x - 1
theorem spec_true (x : Int) : solution x true = x + 1 := by rfl
theorem test_true : solution 3 true = 4 := by decide
theorem test_false : solution 3 false = 2 := by decide
end Tiny
#print axioms Tiny.spec_true
#print axioms Tiny.test_true
#print axioms Tiny.test_false

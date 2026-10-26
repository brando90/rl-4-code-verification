import Mathlib
namespace Tiny
def solution (x : Int) (opt : Option Int) : Int := opt.getD x
theorem spec_none (x : Int) : solution x none = x := by rfl
theorem spec_some (x value : Int) : solution x (some value) = value := by rfl
theorem test_default : solution 4 none = 4 := by decide
theorem test_value : solution 4 (some (-2)) = -2 := by decide
end Tiny
#print axioms Tiny.spec_none
#print axioms Tiny.spec_some
#print axioms Tiny.test_default
#print axioms Tiny.test_value

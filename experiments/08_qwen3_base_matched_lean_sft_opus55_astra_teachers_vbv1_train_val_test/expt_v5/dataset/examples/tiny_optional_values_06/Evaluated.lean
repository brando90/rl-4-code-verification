import Mathlib
namespace Tiny
def solution (opt : Option Int) : Option Int := opt.map (fun x => x + 1)
theorem spec_some (x : Int) : solution (some x) = some (x + 1) := by rfl
theorem test_none : solution none = none := by decide
theorem test_value : solution (some (-2)) = some (-1) := by decide
end Tiny
#print axioms Tiny.spec_some
#print axioms Tiny.test_none
#print axioms Tiny.test_value

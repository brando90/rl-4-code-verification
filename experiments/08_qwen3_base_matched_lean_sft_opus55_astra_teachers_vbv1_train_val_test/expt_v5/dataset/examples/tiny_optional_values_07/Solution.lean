import Mathlib
namespace Tiny
def solution (opt : Option Int) : Option Int := opt.map (fun x => -x)
theorem spec_some (x : Int) : solution (some x) = some (-x) := by rfl
theorem test_none : solution none = none := by decide
theorem test_value : solution (some (-2)) = some 2 := by decide
end Tiny

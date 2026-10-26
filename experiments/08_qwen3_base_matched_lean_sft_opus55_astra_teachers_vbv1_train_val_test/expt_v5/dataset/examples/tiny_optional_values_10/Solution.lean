import Mathlib
namespace Tiny
def solution (x : Int) (opt : Option Int) : Option Int := opt.map (fun value => value - x)
theorem spec_some (x value : Int) : solution x (some value) = some (value - x) := by rfl
theorem test_none : solution 4 none = none := by decide
theorem test_value : solution (-3) (some 2) = some 5 := by decide
end Tiny

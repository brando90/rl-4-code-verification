import Mathlib
namespace Tiny
def solution (x : Int) (p : Bool) (opt : Option Int) : Option Int := match opt with | some value => some value | none => if p then some x else none
theorem spec_some (x : Int) (p : Bool) (value : Int) : solution x p (some value) = some value := by rfl
theorem test_value : solution 3 false (some (-2)) = some (-2) := by decide
theorem test_fallback : solution 3 true none = some 3 := by decide
end Tiny
